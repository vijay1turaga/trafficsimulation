import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def plot_speed_vs_time():
    df = pd.read_csv('data/sample_dataset.csv')
    plt.figure(figsize=(10, 6))
    for veh_id in df['vehicle_id'].unique()[:5]:  # Plot first 5 vehicles
        veh_data = df[df['vehicle_id'] == veh_id]
        plt.plot(veh_data['timestamp'], veh_data['speed'], label=f'Vehicle {veh_id}')
    plt.xlabel('Time (s)')
    plt.ylabel('Speed (m/s)')
    plt.title('Speed vs Time for Sample Vehicles')
    plt.legend()
    plt.savefig('speed_vs_time.png')
    plt.show()

def plot_latency_vs_congestion():
    df = pd.read_csv('data/sample_dataset.csv')
    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=df, x='latency', y='congestion', alpha=0.6)
    plt.xlabel('Latency (s)')
    plt.ylabel('Congestion (0=Free, 1=Congested)')
    plt.title('Latency vs Congestion')
    plt.savefig('latency_vs_congestion.png')
    plt.show()

def plot_pdr_vs_density():
    # Simulate density and PDR relationship
    density = np.random.uniform(0, 1, 100)
    pdr = 1 - density * 0.5  # PDR decreases with density
    plt.figure(figsize=(8, 6))
    plt.scatter(density, pdr, alpha=0.6)
    plt.xlabel('Traffic Density')
    plt.ylabel('Packet Delivery Ratio (PDR)')
    plt.title('PDR vs Traffic Density')
    plt.savefig('pdr_vs_density.png')
    plt.show()

if __name__ == "__main__":
    plot_speed_vs_time()
    plot_latency_vs_congestion()
    plot_pdr_vs_density()