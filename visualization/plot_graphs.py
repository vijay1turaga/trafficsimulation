import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import seaborn as sns


def load_dataset():
    fused_path = 'data/fused_dataset.csv'
    fallback_path = 'data/sample_dataset.csv'
    if os.path.exists(fused_path):
        df = pd.read_csv(fused_path)
        print(f"Loaded fused dataset shape: {df.shape}, columns: {list(df.columns)}")
        return df
    if os.path.exists(fallback_path):
        df = pd.read_csv(fallback_path)
        print(f"Loaded sample dataset shape: {df.shape}, columns: {list(df.columns)}")
        return df
    raise FileNotFoundError('No dataset found. Run the hybrid ingestion pipeline first.')


def plot_speed_vs_time():
    df = load_dataset()
    plt.figure(figsize=(12, 6))
    unique_vehs = df['vehicle_id'].unique()[:5]
    print(f"Plotting {len(unique_vehs)} vehicles: {unique_vehs}")
    for veh_id in unique_vehs:
        veh_data = df[df['vehicle_id'] == veh_id]
        if len(veh_data) > 0:
            plt.plot(veh_data['timestamp'], veh_data['speed'], label=f'Vehicle {veh_id}', linewidth=2)
    plt.xlabel('Time (s)')
    plt.ylabel('Speed (m/s)')
    plt.title('Vehicle Speed Profiles Over Time', fontweight='bold')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig('visualization/speed_vs_time.png', dpi=300, bbox_inches='tight')
    plt.show()


def plot_latency_vs_congestion():
    df = load_dataset()
    plt.figure(figsize=(10, 6))
    
    # Safe aggregation - handle missing congestion column
    if 'congestion' not in df.columns:
        df['congestion'] = (df['speed'] < 2.0).astype(int)
        print("'congestion' created from speed < 2.0")
    
    # Simple groupby agg (no multi-index issues)
    summary_stats = df.groupby('congestion')['latency'].agg(['count', 'mean', 'std']).round(3)
    summary_stats.columns = ['n_samples', 'mean_latency', 'std_latency']
    summary_stats['n_samples'] = summary_stats['n_samples'].astype(int)
    
    x_pos = [0.4, 0.6]
    colors = ['#28a745', '#dc3545']
    errors = summary_stats['std_latency'].values
    
    print("Latency debug:", summary_stats)
    
    bars = plt.bar(x_pos, summary_stats['mean_latency'], yerr=errors, capsize=8, 
                   color=colors, alpha=0.8, width=0.15, edgecolor='white', linewidth=2)
    
    plt.xticks(x_pos, [
        f'No Traffic Jam\n({summary_stats.loc[0, "n_samples"]} vehicles)', 
        f'Traffic Jam\n({summary_stats.loc[1, "n_samples"]} vehicles)'
    ])
    plt.ylabel('Average Latency (seconds)')
    plt.title('Network Latency During Traffic Conditions', fontweight='bold', fontsize=14)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('visualization/latency_vs_congestion.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"✅ Latency Analysis:")
    print(f"   No jam: {summary_stats.loc[0, 'mean_latency']:.3f}s ± {summary_stats.loc[0, 'std_latency']:.3f}s ({summary_stats.loc[0, 'n_samples']} samples)")
    print(f"   Jam: {summary_stats.loc[1, 'mean_latency']:.3f}s ± {summary_stats.loc[1, 'std_latency']:.3f}s ({summary_stats.loc[1, 'n_samples']} samples)")


def plot_pdr_vs_density():
    df = load_dataset()
    
    # Safe density calculation
    if 'density' not in df.columns and 'density_proxy' in df.columns:
        df['density'] = df['density_proxy']
    elif 'density' not in df.columns:
        df['density'] = df.groupby('timestamp')['vehicle_id'].transform('size')
    
    df['density_decile'] = pd.qcut(df['density'].rank(method='first'), 10, labels=False)
    pdr_density = df.groupby('density_decile')['pdr'].agg(['mean', 'count']).reset_index()
    
    print(f"PDR debug: {len(pdr_density)} deciles")
    
    plt.figure(figsize=(10, 6))
    plt.plot(pdr_density['density_decile'] * 10, pdr_density['mean'], 
             marker='o', linewidth=4, markersize=10, color='#e67e22')
    plt.fill_between(pdr_density['density_decile'] * 10, 
                     pdr_density['mean'] - 0.03, 
                     pdr_density['mean'] + 0.03, alpha=0.3, color='#e67e22')
    
    plt.xlabel('Traffic Density Decile (%)')
    plt.ylabel('Average Packet Delivery Ratio')
    plt.title('PDR Degradation vs Traffic Density', fontweight='bold', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('visualization/pdr_vs_density.png', dpi=300, bbox_inches='tight')
    plt.show()
    print("✅ Real PDR vs density curve generated")


if __name__ == "__main__":
    plot_speed_vs_time()
    plot_latency_vs_congestion()
    plot_pdr_vs_density()

