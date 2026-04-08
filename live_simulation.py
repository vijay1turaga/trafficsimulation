"""
Live Traffic Simulation Visualization - Simplified Version
Real-time display of vehicle positions and stats
"""

import os
import sys
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from datetime import datetime

# Add SUMO tools to path
sumo_home = r'C:\Program Files (x86)\Eclipse\Sumo'
if 'SUMO_HOME' in os.environ:
    sumo_home = os.environ['SUMO_HOME']

tools = os.path.join(sumo_home, 'tools')
sys.path.append(tools)

import traci

# Network geometry
NETWORK_BOUNDS = {
    'xmin': 0,
    'xmax': 1000,
    'ymin': 0,
    'ymax': 1000
}

class LiveTrafficVisualizer:
    def __init__(self):
        self.sumo_binary = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"
        self.config_file = r"C:\Users\Vijay\OneDrive\Desktop\traffic\sumo_config\manhattan.sumocfg"
        self.step = 0
        self.start_time = None
        self.vehicle_speeds = {}
        self.vehicle_positions = {}
        
    def start_simulation(self):
        """Start SUMO with TraCI"""
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
        """Run simulation and update visualization every few steps"""
        
        try:
            self.start_simulation()
            elapsed_sim = 0
            last_plot_step = -10
            
            print("\n✅ SUMO Connection Established")
            print("📊 Running live simulation...\n")
            
            # Create figure for live updates
            fig, axes = plt.subplots(2, 2, figsize=(14, 12))
            fig.suptitle('V2X-Predict: Live Traffic Monitoring & Analytics', 
                        fontsize=14, fontweight='bold')
            
            plt.ion()  # Turn on interactive mode
            
            vehicle_trajectories = {}
            timestamps = []
            avg_speeds = []
            vehicle_counts = []
            congestion_counts = []
            
            while traci.simulation.getMinExpectedNumber() > 0 and self.step < num_steps:
                # Run simulation step
                traci.simulationStep()
                self.step += 1
                elapsed_sim = self.step * 0.1  # Each step is 100ms
                
                # Get vehicle data
                vehicle_ids = traci.vehicle.getIDList()
                current_speeds = []
                congested = 0
                
                self.vehicle_positions = {}
                self.vehicle_speeds = {}
                
                for vid in vehicle_ids:
                    try:
                        x, y = traci.vehicle.getPosition(vid)
                        speed = traci.vehicle.getSpeed(vid)
                        
                        self.vehicle_positions[vid] = (x, y)
                        self.vehicle_speeds[vid] = speed
                        current_speeds.append(speed)
                        
                        # Track trajectory
                        if vid not in vehicle_trajectories:
                            vehicle_trajectories[vid] = {'x': [], 'y': [], 'speed': [], 'time': []}
                        vehicle_trajectories[vid]['x'].append(x)
                        vehicle_trajectories[vid]['y'].append(y)
                        vehicle_trajectories[vid]['speed'].append(speed)
                        vehicle_trajectories[vid]['time'].append(elapsed_sim)
                        
                        if speed < 2.0:
                            congested += 1
                            
                    except Exception as e:
                        pass
                
                # Update metrics every 10 steps
                if self.step % 10 == 0:
                    timestamps.append(elapsed_sim)
                    avg_speeds.append(np.mean(current_speeds) if current_speeds else 0)
                    vehicle_counts.append(len(vehicle_ids))
                    congestion_counts.append(congested)
                    
                    # Update plots
                    try:
                        # Clear all axes
                        for ax in axes.flat:
                            ax.clear()
                        
                        # Plot 1: Network Map with Vehicles
                        ax1 = axes[0, 0]
                        self._plot_network(ax1)
                        self._plot_vehicles(ax1, vehicle_trajectories)
                        ax1.set_title(f'Traffic Network [t={elapsed_sim:.1f}s]', 
                                    fontweight='bold')
                        ax1.set_xlim(-100, 1100)
                        ax1.set_ylim(-100, 1100)
                        ax1.grid(True, alpha=0.2)
                        
                        # Plot 2: Speed vs Time
                        ax2 = axes[0, 1]
                        if timestamps:
                            ax2.plot(timestamps, avg_speeds, 'b-o', linewidth=2, markersize=4)
                            ax2.set_xlabel('Simulation Time (s)')
                            ax2.set_ylabel('Average Speed (m/s)')
                            ax2.set_title('Network Speed Profile', fontweight='bold')
                            ax2.grid(True, alpha=0.3)
                            ax2.set_ylim(0, 15)
                        
                        # Plot 3: Vehicle Count
                        ax3 = axes[1, 0]
                        if timestamps:
                            ax3.bar(timestamps, vehicle_counts, width=0.5, color='skyblue', 
                                   edgecolor='navy', alpha=0.7)
                            ax3.set_xlabel('Simulation Time (s)')
                            ax3.set_ylabel('Active Vehicles')
                            ax3.set_title('Vehicle Count', fontweight='bold')
                            ax3.grid(True, alpha=0.3, axis='y')
                        
                        # Plot 4: Congestion Index
                        ax4 = axes[1, 1]
                        if timestamps:
                            ax4.fill_between(timestamps, congestion_counts, alpha=0.5, color='red')
                            ax4.plot(timestamps, congestion_counts, 'r-o', linewidth=2, markersize=4)
                            ax4.set_xlabel('Simulation Time (s)')
                            ax4.set_ylabel('Congested Vehicles (speed < 2.0 m/s)')
                            ax4.set_title('Congestion Trend', fontweight='bold')
                            ax4.grid(True, alpha=0.3)
                        
                        plt.tight_layout()
                        plt.pause(0.01)  # Update display
                        
                    except Exception as e:
                        print(f"Plot error: {e}")
                
                # Print status every 50 steps
                if self.step % 50 == 0:
                    elapsed_real = time.time() - self.start_time
                    print(f"⏱️  Sim Time: {elapsed_sim:6.1f}s | Vehicles: {len(vehicle_ids):2d} | " +
                          f"Avg Speed: {np.mean(current_speeds) if current_speeds else 0:5.2f} m/s | " +
                          f"Congested: {congested:2d} | Real: {elapsed_real:6.2f}s")
            
            print(f"\n✅ Simulation Complete!")
            print(f"   Total simulation time: {elapsed_sim:.1f} seconds")
            print(f"   Total real time: {time.time() - self.start_time:.2f} seconds")
            print(f"   Vehicle-steps recorded: {sum(len(v['time']) for v in vehicle_trajectories.values())}")
            
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
        """Plot the Manhattan network"""
        # Roads
        ax.plot([250, 250], [0, 1000], 'k-', linewidth=3, alpha=0.4)
        ax.plot([750, 750], [0, 1000], 'k-', linewidth=3, alpha=0.4)
        ax.plot([0, 1000], [250, 250], 'k-', linewidth=3, alpha=0.4)
        ax.plot([0, 1000], [750, 750], 'k-', linewidth=3, alpha=0.4)
        
        # Junctions
        junctions = [(250, 250), (250, 750), (750, 250), (750, 750)]
        for jx, jy in junctions:
            circle = patches.Circle((jx, jy), 40, color='gray', alpha=0.3)
            ax.add_patch(circle)
            ax.text(jx, jy, 'J', ha='center', va='center', fontsize=10, fontweight='bold')
    
    def _plot_vehicles(self, ax, trajectories):
        """Plot vehicles and their trajectories"""
        colors = ['red', 'blue', 'green', 'orange', 'purple']
        
        for idx, (vid, data) in enumerate(trajectories.items()):
            color = colors[idx % len(colors)]
            
            # Plot trajectory
            if len(data['x']) > 1:
                ax.plot(data['x'], data['y'], color=color, alpha=0.3, linewidth=1, 
                       label=f'{vid} trajectory')
            
            # Plot current position
            if data['x'] and data['y']:
                speed = data['speed'][-1] if data['speed'] else 0
                size = 100 + speed * 20
                ax.scatter(data['x'][-1], data['y'][-1], s=size, c=color, 
                          edgecolors='black', linewidth=1.5, zorder=10, alpha=0.8)
                
                # Add label
                ax.text(data['x'][-1], data['y'][-1], f"{vid[-1]}", 
                       ha='center', va='center', fontsize=9, fontweight='bold', color='white')

def main():
    print("\n" + "="*70)
    print("  V2X-PREDICT: LIVE TRAFFIC SIMULATION")
    print("="*70)
    print("\n📍 Network: Manhattan 4-junction grid (1000m x 1000m)")
    print("🚗 Vehicles: 3 cars with pre-defined routes")
    print("⏱️  Duration: 55.8 seconds of simulated time")
    print("\n📊 Visualization Features:")
    print("   • Real-time network view with vehicle positions")
    print("   • Speed profile graph showing average network speed over time")
    print("   • Active vehicle count")
    print("   • Congestion index (vehicles moving < 2.0 m/s)")
    print("\n🎨 Vehicle Display:")
    print("   • Color-coded trajectories for each vehicle")
    print("   • Circle size indicates current speed")
    print("   • Real-time position updates every 1 second of sim time")
    print("\n" + "="*70 + "\n")
    
    visualizer = LiveTrafficVisualizer()
    visualizer.run_and_visualize(num_steps=600)

if __name__ == '__main__':
    main()
