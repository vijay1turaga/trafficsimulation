"""
Live Traffic Simulation Visualization with runtime model prediction alerts.
"""

import os
import sys
import time
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
import joblib
try:
    import tensorflow as tf
    print("TensorFlow imported successfully")
except ImportError:
    tf = None
    print("TensorFlow not available, using rule-based predictions.")
from collections import defaultdict

# Add SUMO tools and controller path to Python module path
sumo_home = r'C:\Program Files (x86)\Eclipse\Sumo'
if 'SUMO_HOME' in os.environ:
    sumo_home = os.environ['SUMO_HOME']

tools = os.path.join(sumo_home, 'tools')
sys.path.append(tools)
sys.path.append(os.path.join(os.getcwd(), 'python_controller'))

import traci
from python_controller.bilstm_model import predict_congestion

NETWORK_BOUNDS = {
    'xmin': 0,
    'xmax': 1000,
    'ymin': 0,
    'ymax': 1000
}

MODEL_PATH = 'models/bilstm_model.h5'
SCALER_PATH = 'models/scaler.save'
QOS_METRICS_PATH = 'data/qos_metrics.csv'


def get_vehicle_color(speed, max_speed=13.89):
    speed_ratio = speed / max_speed
    if speed < 0.1:
        return 'darkred'
    elif speed_ratio > 0.7:
        return 'green'
    elif speed_ratio > 0.4:
        return 'yellow'
    else:
        return 'red'


class LiveTrafficVisualizer:
    def __init__(self):
        self.sumo_binary = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"
        self.config_file = r"C:\Users\Vijay\OneDrive\Desktop\traffic\sumo_config\manhattan.sumocfg"
        self.step = 0
        self.start_time = None
        self.vehicle_speeds = {}
        self.vehicle_positions = {}
        self.feature_buffer = defaultdict(list)
        self.time_steps = 15
        self.model = self.load_prediction_model()
        self.scaler = self.load_scaler()
        self.qos_metrics = self.load_qos_metrics()
        print(f"Model loaded: {self.model is not None}, Scaler loaded: {self.scaler is not None}, QoS shape: {self.qos_metrics.shape if not self.qos_metrics.empty else 'empty'}")
        os.makedirs('live_plots', exist_ok=True)
    
    def load_prediction_model(self):


        if tf is None or not os.path.exists(MODEL_PATH):
            print(f"No TF or model {MODEL_PATH}, using rule-based.")
            return None
        try:
            print(f"Loading prediction model from {MODEL_PATH}")
            return tf.keras.models.load_model(MODEL_PATH)
        except Exception as e:
            print(f"Model load failed: {e}. Using rule-based.")
            return None


    def load_scaler(self):
        if os.path.exists(SCALER_PATH):
            try:
                scaler = joblib.load(SCALER_PATH)
                print(f"Scaler loaded successfully")
                return scaler
            except Exception as e:
                print(f"Scaler load failed: {e}")
        return None

    def load_qos_metrics(self):
        if os.path.exists(QOS_METRICS_PATH):
            try:
                df = pd.read_csv(QOS_METRICS_PATH)
                print(f"QoS metrics loaded: {df.shape}")
                if 'time' in df.columns and 'source_node' in df.columns:
                    return df
            except Exception as e:
                print(f"QoS load failed: {e}")
        return pd.DataFrame()

    def get_source_node(self, vehicle_id):
        if isinstance(vehicle_id, str) and vehicle_id.startswith('veh_'):
            try:
                return int(vehicle_id.split('_')[-1])
            except ValueError:
                pass
        return 0

    def lookup_qos(self, source_node, timestamp):
        if self.qos_metrics.empty:
            return 1.0, 0.1
        current_time = round(timestamp, 1)
        candidates = self.qos_metrics[(self.qos_metrics['source_node'] == source_node) & (self.qos_metrics['time'] == current_time)]
        if not candidates.empty:
            return float(candidates.iloc[0]['PDR']), float(candidates.iloc[0]['Latency'])
        candidates = self.qos_metrics[self.qos_metrics['source_node'] == source_node]
        if not candidates.empty:
            return float(candidates['PDR'].mean()), float(candidates['Latency'].mean())
        return 1.0, 0.1

    def start_simulation(self):
        print("\n🚀 Starting SUMO Traffic Simulation...")
        traci.start([
            self.sumo_binary,
            "-c", self.config_file,
            "--start",
            "--no-warnings",
            "--begin", "0"
        ])
        self.start_time = time.time()

    def run_and_visualize(self, num_steps=600):
        try:
            self.start_simulation()
            elapsed_sim = 0
            vehicle_trajectories = {}
            timestamps = []
            avg_speeds = []
            vehicle_counts = []
            congestion_counts = []
            alerts = 0


            plt.style.use('dark_background')
            fig = plt.figure(figsize=(16, 12), facecolor='#0f0f23')
            fig.patch.set_facecolor('#0f0f23')
            axes = fig.subplots(2, 2)
            for ax in axes.flat:
                ax.set_facecolor('#1a1a2e')
            plt.ion()


            while traci.simulation.getMinExpectedNumber() > 0 and self.step < num_steps:
                traci.simulationStep()


                self.step += 1
                elapsed_sim = self.step * 0.1

                vehicle_ids = traci.vehicle.getIDList()
                current_speeds = []
                congested = 0

                self.vehicle_positions = {}
                self.vehicle_speeds = {}

                for vid in vehicle_ids:
                    try:
                        x, y = traci.vehicle.getPosition(vid)
                        speed = traci.vehicle.getSpeed(vid)
                        accel = traci.vehicle.getAcceleration(vid)

                        self.vehicle_positions[vid] = (x, y)
                        self.vehicle_speeds[vid] = speed
                        current_speeds.append(speed)

                        if vid not in vehicle_trajectories:
                            vehicle_trajectories[vid] = {'x': [], 'y': [], 'speed': [], 'time': []}
                        vehicle_trajectories[vid]['x'].append(x)
                        vehicle_trajectories[vid]['y'].append(y)
                        vehicle_trajectories[vid]['speed'].append(speed)
                        vehicle_trajectories[vid]['time'].append(elapsed_sim)

                        if speed < 2.0:
                            congested += 1

                        source_node = self.get_source_node(vid)
                        pdr, latency = self.lookup_qos(source_node, elapsed_sim)
                        feature_vector = np.array([speed, accel, x, y, pdr, latency], dtype=np.float32)
                        if self.scaler is not None:
                            try:
                                feature_vector = self.scaler.transform(feature_vector.reshape(1, -1)).flatten()
                            except Exception as e:
                                print(f"Scaler transform error for {vid}: {e}")
                                feature_vector = np.zeros(6)
                        self.feature_buffer[vid].append(feature_vector)
                        if len(self.feature_buffer[vid]) > self.time_steps:
                            self.feature_buffer[vid].pop(0)
                        if len(self.feature_buffer[vid]) == self.time_steps:
                            if self.model is not None:
                                try:
                                    X_seq = np.expand_dims(np.array(self.feature_buffer[vid]), axis=0)
                                    pred, conf = predict_congestion(self.model, X_seq)
                                except Exception as e:
                                    print(f"Prediction error for {vid}: {e}")
                                    pred = [0]
                                    conf = [0.0]
                            else:
                                pred = [1 if speed < 2.0 else 0]
                                conf = [1.0]
                            if pred[0] == 1 and conf[0] > 0.7:  # High confidence only
                                alerts += 1
                                alert_msg = f"🚨 ALERT t={elapsed_sim:.1f}s {vid} conf={conf[0]:.2f}"
                                print(alert_msg)


                    except Exception:
                        pass

                if self.step % 10 == 0:
                    if not timestamps:
                        continue
                    
                    timestamps.append(elapsed_sim)
                    avg_speeds.append(np.mean(current_speeds) if current_speeds else 0)
                    vehicle_counts.append(len(vehicle_ids))
                    congestion_counts.append(congested)


                    for ax in axes.flat:
                        ax.clear()

                    ax1 = axes[0, 0]
                    self._plot_network(ax1)
                    self._plot_vehicles(ax1, vehicle_trajectories)
                    ax1.set_title(f'Traffic Network [t={elapsed_sim:.1f}s]', fontweight='bold')
                    ax1.set_xlim(-100, 1100)
                    ax1.set_ylim(-100, 1100)
                    ax1.grid(True, alpha=0.2)

                    ax2 = axes[0, 1]
                    ax2.plot(timestamps, avg_speeds, 'b-o', linewidth=2, markersize=4)
                    ax2.set_xlabel('Simulation Time (s)')
                    ax2.set_ylabel('Average Speed (m/s)')
                    ax2.set_title('Network Speed Profile', fontweight='bold')
                    ax2.grid(True, alpha=0.3)
                    ax2.set_ylim(0, 15)

                    ax3 = axes[1, 0]
                    ax3.bar(timestamps, vehicle_counts, width=0.5, color='skyblue', edgecolor='navy', alpha=0.7)
                    ax3.set_xlabel('Simulation Time (s)')
                    ax3.set_ylabel('Active Vehicles')
                    ax3.set_title('Vehicle Count', fontweight='bold')
                    ax3.grid(True, alpha=0.3, axis='y')

                    ax4 = axes[1, 1]
                    ax4.fill_between(timestamps, congestion_counts, alpha=0.5, color='red')
                    ax4.plot(timestamps, congestion_counts, 'r-o', linewidth=2, markersize=4)
                    ax4.set_xlabel('Simulation Time (s)')
                    ax4.set_ylabel('Congested Vehicles (speed < 2.0 m/s)')
                    ax4.set_title('Congestion Trend', fontweight='bold')
                    ax4.grid(True, alpha=0.3)

                    plt.tight_layout()

                    # Proper plot rendering before save
                    fig.canvas.draw()
                    fig.canvas.flush_events()
                    
                    # Save with explicit background
                    plt.savefig(f'live_plots/step_{self.step}.png', dpi=150, bbox_inches='tight', 
                              facecolor='#0f0f23', edgecolor='none')
                    plt.pause(0.001)  # Ultra-fast for smooth sim




                if self.step % 50 == 0:
                    elapsed_real = time.time() - self.start_time
                    print(f"⏱️  Sim Time: {elapsed_sim:6.1f}s | Vehicles: {len(vehicle_ids):2d} | Avg Speed: {np.mean(current_speeds) if current_speeds else 0:5.2f} m/s | Congested: {congested:2d} | Alerts: {alerts} | Real: {elapsed_real:6.2f}s")

            print(f"\n✅ Simulation Complete! Total alerts: {alerts}")
            plt.show(block=True)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                if traci.isLoaded():
                    traci.close()
                print("✅ Simulation closed successfully\n")
            except:
                pass

    def _plot_network(self, ax):
        ax.plot([250, 250], [0, 1000], 'k-', linewidth=3, alpha=0.4)
        ax.plot([750, 750], [0, 1000], 'k-', linewidth=3, alpha=0.4)
        ax.plot([0, 1000], [250, 250], 'k-', linewidth=3, alpha=0.4)
        ax.plot([0, 1000], [750, 750], 'k-', linewidth=3, alpha=0.4)
        junctions = [(250, 250), (250, 750), (750, 250), (750, 750)]
        for jx, jy in junctions:
            circle = patches.Circle((jx, jy), 40, color='gray', alpha=0.3)
            ax.add_patch(circle)
            ax.text(jx, jy, 'J', ha='center', va='center', fontsize=10, fontweight='bold')

    def _plot_vehicles(self, ax, trajectories):
        colors = ['red', 'blue', 'green', 'orange', 'purple']
        for idx, (vid, data) in enumerate(trajectories.items()):
            color = colors[idx % len(colors)]
            if len(data['x']) > 1:
                ax.plot(data['x'], data['y'], color=color, alpha=0.3, linewidth=1, label=f'{vid} trajectory')
            if data['x'] and data['y']:
                speed = data['speed'][-1] if data['speed'] else 0
                ax.scatter(data['x'][-1], data['y'][-1], s=100 + speed * 20, c=color, edgecolors='black', linewidth=1.5, zorder=10, alpha=0.8)
                ax.text(data['x'][-1], data['y'][-1], f"{vid[-2:]}", ha='center', va='center', fontsize=9, fontweight='bold', color='white')


def main():
    print("\n" + "="*70)
    print("  V2X-PREDICT: LIVE TRAFFIC SIMULATION")
    print("="*70)
    visualizer = LiveTrafficVisualizer()
    visualizer.run_and_visualize(num_steps=600)


if __name__ == '__main__':
    main()

