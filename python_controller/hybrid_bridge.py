import os
import subprocess
import pandas as pd

from python_controller.data_fusion import build_fused_dataset
from python_controller.traci_controller import run_sumo_simulation


def find_waf_runner(ns3_dir):
    candidates = ['waf.bat', 'waf.exe', 'waf']
    for candidate in candidates:
        path = os.path.join(ns3_dir, candidate)
        if os.path.exists(path):
            return [path]
    return None


def generate_fallback_qos(ns3_dir):
    print("Generating fallback QoS metrics from SUMO mobility trace...")
    trace_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sumo_mobility_trace.csv')
    qos_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'qos_metrics.csv')

    if not os.path.exists(trace_path):
        raise FileNotFoundError(f"SUMO mobility trace required for fallback QoS: {trace_path}")

    df = pd.read_csv(trace_path)
    df['timestamp'] = df['timestamp'].round(1)

    grouped = df.groupby(['source_node', 'timestamp']).agg(
        vehicle_count=('vehicle_id', 'nunique'),
        avg_speed=('speed', 'mean')
    ).reset_index()

    grouped['PDR'] = grouped.apply(lambda row: max(0.4, min(1.0, 1.0 - 0.3 * min(1.0, row.vehicle_count / 30.0) + 0.1 * min(1.0, row.avg_speed / 30.0))), axis=1)
    grouped['Latency'] = grouped.apply(lambda row: max(0.05, min(1.0, 0.05 + 0.04 * row.vehicle_count + 0.02 * max(0.0, 10.0 - row.avg_speed))), axis=1)
    grouped['TxPackets'] = grouped['vehicle_count'] * 10
    grouped['RxPackets'] = (grouped['TxPackets'] * grouped['PDR']).astype(int)
    grouped['TxBytes'] = grouped['TxPackets'] * 512
    grouped['RxBytes'] = grouped['RxPackets'] * 512
    grouped['dest_node'] = grouped['source_node']

    fallback = grouped[['timestamp', 'source_node', 'dest_node', 'TxPackets', 'RxPackets', 'TxBytes', 'RxBytes', 'PDR', 'Latency']]
    fallback.to_csv(qos_file, index=False)

    print(f"Fallback QoS metrics written to {qos_file}")
    return qos_file


def run_ns3_simulation():
    ns3_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'ns3_scripts'))
    qos_file = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data', 'qos_metrics.csv'))

    if os.path.exists(qos_file):
        print(f"Found existing QoS metrics: {qos_file}")
        return qos_file

    waf_cmd = find_waf_runner(ns3_dir)
    if waf_cmd is not None:
        command = waf_cmd + ['--run', 'vanet_simulation']
        print(f"Running NS-3 with: {command}")
        try:
            subprocess.run(command, cwd=ns3_dir, check=True)
        except subprocess.CalledProcessError as exc:
            print(f"NS-3 simulation returned non-zero exit code: {exc}")
        except FileNotFoundError:
            print("Found waf runner path but could not execute it.")
        else:
            if os.path.exists(qos_file):
                return qos_file
            print("NS-3 runner completed but QoS output was not produced.")
    else:
        print("No NS-3 waf runner found in ns3_scripts/; skipping native NS-3 execution.")

    return generate_fallback_qos(ns3_dir)


def run_hybrid_pipeline(scenario='medium'):
    print("Starting SUMO ingestion...")
    run_sumo_simulation(scenario=scenario)
    print("Starting NS-3 synchronization and QoS collection...")
    run_ns3_simulation()
    print("Building fused dataset from SUMO and NS-3 outputs...")
    build_fused_dataset()
    print("Hybrid ingestion pipeline complete.")


if __name__ == '__main__':
    run_hybrid_pipeline()
