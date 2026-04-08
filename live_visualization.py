"""
Live Traffic Simulation Visualization
Real-time animated visualization of vehicles in the Manhattan network
"""

import os
import sys
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle
import numpy as np

# Add SUMO tools to path
sumo_home = r'C:\Program Files (x86)\Eclipse\Sumo'
if 'SUMO_HOME' in os.environ:
    sumo_home = os.environ['SUMO_HOME']

tools = os.path.join(sumo_home, 'tools')
sys.path.append(tools)

import traci

# Network geometry (Manhattan grid)
NETWORK_BOUNDS = {
    'xmin': 0,
    'xmax': 1000,
    'ymin': 0,
    'ymax': 1000
}

# Vehicle colors
VEHICLE_COLORS = {
    'fast': 'green',
    'medium': 'yellow',
    'slow': 'red',
    'stopped': 'darkred'
}

def get_vehicle_color(speed, max_speed=13.89):
    """Determine vehicle color based on speed"""
    speed_ratio = speed / max_speed
    if speed < 0.1:
        return VEHICLE_COLORS['stopped']
    elif speed_ratio > 0.7:
        return VEHICLE_COLORS['fast']
    elif speed_ratio > 0.4:
        return VEHICLE_COLORS['medium']
    else:
        return VEHICLE_COLORS['slow']

def start_sumo(sumo_binary):
    """Start SUMO simulation"""
    sumocfg = r"C:\Users\Vijay\OneDrive\Desktop\traffic\sumo_config\manhattan.sumocfg"
    traci.start([
        sumo_binary,
        "-c", sumocfg,
        "--start",
        "--no-warnings"
    ])

class TrafficSimulator:
    def __init__(self):
        self.vehicle_data = {}
        self.step = 0
        self.max_speed = 13.89  # m/s
        self.congestion_threshold = 2.0  # m/s
        
    def update(self, frame):
        """Update simulation and return vehicle positions"""
        if not traci.simulation.isLoaded():
            return
            
        traci.simulationStep()
        self.step += 1
        
        # Get all active vehicles
        vehicle_ids = traci.vehicle.getIDList()
        
        self.vehicle_data = {}
        congested_vehicles = 0
        
        for vehicle_id in vehicle_ids:
            try:
                x, y = traci.vehicle.getPosition(vehicle_id)
                speed = traci.vehicle.getSpeed(vehicle_id)
                accel = traci.vehicle.getAcceleration(vehicle_id)
                route = traci.vehicle.getRouteID(vehicle_id)
                
                self.vehicle_data[vehicle_id] = {
                    'x': x,
                    'y': y,
                    'speed': speed,
                    'acceleration': accel,
                    'route': route,
                    'color': get_vehicle_color(speed)
                }
                
                if speed < self.congestion_threshold:
                    congested_vehicles += 1
                    
            except Exception as e:
                pass
        
        # Check if simulation ended
        if traci.simulation.getMinExpectedNumber() == 0:
            traci.close()
            
        return self.vehicle_data, congested_vehicles

def plot_network(ax):
    """Plot the network roads"""
    # Vertical roads
    ax.plot([250, 250], [0, 1000], 'k-', linewidth=2, alpha=0.3)
    ax.plot([750, 750], [0, 1000], 'k-', linewidth=2, alpha=0.3)
    
    # Horizontal roads
    ax.plot([0, 1000], [250, 250], 'k-', linewidth=2, alpha=0.3)
    ax.plot([0, 1000], [750, 750], 'k-', linewidth=2, alpha=0.3)
    
    # Junctions
    junctions = [(250, 250), (250, 750), (750, 250), (750, 750)]
    for jx, jy in junctions:
        circle = plt.Circle((jx, jy), 50, color='gray', alpha=0.5)
        ax.add_patch(circle)

def animate(frame, simulator, ax, fig, title_text):
    """Animation function"""
    ax.clear()
    
    # Plot network
    plot_network(ax)
    
    # Update simulation
    try:
        vehicle_data, congested = simulator.update(frame)
    except:
        return
    
    # Plot vehicles
    if vehicle_data:
        for vehicle_id, data in vehicle_data.items():
            # Vehicle body (triangle pointing in direction of movement)
            x, y = data['x'], data['y']
            speed = data['speed']
            
            # Draw vehicle as circle with color based on speed
            circle = plt.Circle((x, y), 15, color=data['color'], 
                               edgecolor='black', linewidth=1.5, zorder=10)
            ax.add_patch(circle)
            
            # Add vehicle ID
            ax.text(x, y, vehicle_id[-1], ha='center', va='center', 
                   fontsize=8, fontweight='bold', color='white')
            
            # Draw velocity vector
            if speed > 0.5:
                angle = traci.vehicle.getAngle(vehicle_id)
                arrow_len = min(speed * 5, 40)
                dx = arrow_len * np.cos(np.radians(angle))
                dy = arrow_len * np.sin(np.radians(angle))
                ax.arrow(x, y, dx, dy, head_width=8, head_length=5, 
                        fc='black', ec='black', alpha=0.6, zorder=5)
    
    # Set up plot
    ax.set_xlim(NETWORK_BOUNDS['xmin']-50, NETWORK_BOUNDS['xmax']+50)
    ax.set_ylim(NETWORK_BOUNDS['ymin']-50, NETWORK_BOUNDS['ymax']+50)
    ax.set_aspect('equal')
    ax.set_xlabel('X Position (m)', fontsize=10)
    ax.set_ylabel('Y Position (m)', fontsize=10)
    
    # Title with simulation info
    num_vehicles = len(vehicle_data)
    sim_time = simulator.step * 0.1  # 100ms per step
    
    title = f'Live Traffic Simulation | Time: {sim_time:.1f}s | Vehicles: {num_vehicles} | Congested: {congested}'
    ax.set_title(title, fontsize=12, fontweight='bold')
    
    # Legend
    legend_text = (
        "Speed: Green (>70%) | Yellow (40-70%) | Red (<40%) | Dark Red (stopped)\n"
        "Arrows show velocity vectors"
    )
    ax.text(0.02, 0.98, legend_text, transform=ax.transAxes,
           fontsize=9, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    ax.grid(True, alpha=0.2)
    plt.tight_layout()

def main():
    print("\n" + "="*70)
    print("  LIVE TRAFFIC SIMULATION VISUALIZATION")
    print("="*70)
    print("\nStarting SUMO simulation...")
    print("- Network: Manhattan 4-junction grid (1000m x 1000m)")
    print("- Vehicles: 3 cars with defined routes")
    print("- Duration: 55.8 seconds")
    print("\nVisualization Instructions:")
    print("  • Green circles: Fast-moving vehicles")
    print("  • Yellow circles: Medium-speed vehicles")
    print("  • Red circles: Slow-moving vehicles")
    print("  • Dark red circles: Stopped vehicles")
    print("  • Arrows: Velocity vectors (direction & magnitude)")
    print("\n" + "="*70)
    
    sumo_binary = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"
    
    try:
        # Start SUMO
        start_sumo(sumo_binary)
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(12, 10))
        fig.suptitle('V2X-Predict: Real-Time Traffic Monitoring', 
                    fontsize=14, fontweight='bold', y=0.98)
        
        # Create simulator
        simulator = TrafficSimulator()
        
        # Create animation
        print("\n✅ SUMO connection established")
        print("📊 Starting animation...")
        print("⏹️  Close the window to stop the simulation\n")
        
        ani = animation.FuncAnimation(
            fig, animate,
            fargs=(simulator, ax, fig, 'Live Traffic'),
            frames=1000,
            interval=100,  # 100ms per frame
            repeat=False,
            blit=False
        )
        
        plt.show()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure SUMO is installed and C:\\Program Files\\DLR\\Sumo\\bin is in PATH")
        print("2. Check that manhattan.sumocfg exists")
        print("3. Verify Python can connect to SUMO via TraCI")
    finally:
        try:
            if traci.isLoaded():
                traci.close()
            print("\n✅ Simulation closed successfully")
        except:
            pass

if __name__ == '__main__':
    main()
