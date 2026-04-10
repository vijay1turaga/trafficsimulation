import os
import time
from collections import defaultdict

import numpy as np
import pandas as pd
import tensorflow as tf
from python_controller.bilstm_model import predict_congestion
from python_controller.data_fusion import load_sumo_data, load_qos_data, align_and_merge, preprocess_data

DATA_DIR = 'data'
MODEL_PATH = 'models/bilstm_model.h5'


def load_fused_data():
    mobility_df = load_sumo_data()
    qos_df = load_qos_data()
    fused_df = align_and_merge(mobility_df, qos_df)
    processed_df, _ = preprocess_data(fused_df)
    return processed_df


def run_real_time_pipeline(time_steps=15, pause_seconds=0.0):
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}. Train the model first.")

    model = tf.keras.models.load_model(MODEL_PATH)
    fused_df = load_fused_data()
    feature_columns = ['speed', 'acceleration', 'x', 'y', 'pdr', 'latency']

    vehicle_buffers = defaultdict(list)
    alerts = []
    last_alert_time = None

    for _, row in fused_df.sort_values(['timestamp', 'vehicle_id']).iterrows():
        vehicle_id = row['vehicle_id']
        features = row[feature_columns].values.astype(np.float32)
        vehicle_buffers[vehicle_id].append(features)
        if len(vehicle_buffers[vehicle_id]) > time_steps:
            vehicle_buffers[vehicle_id].pop(0)

        if len(vehicle_buffers[vehicle_id]) == time_steps:
            X_seq = np.expand_dims(np.array(vehicle_buffers[vehicle_id]), axis=0)
            prediction, confidence = predict_congestion(model, X_seq)
            if prediction[0] == 1:
                alert = {
                    'timestamp': row['timestamp'],
                    'vehicle_id': vehicle_id,
                    'confidence': float(confidence[0]),
                    'source_node': int(row['source_node'])
                }
                alerts.append(alert)
                if last_alert_time != row['timestamp']:
                    print(f"[ALERT] t={row['timestamp']:.1f}s vehicle={vehicle_id} node={alert['source_node']} congestion predicted confidence={alert['confidence']:.2f}")
                    last_alert_time = row['timestamp']
        if pause_seconds > 0:
            time.sleep(pause_seconds)

    print(f"Realtime prediction complete. Alerts: {len(alerts)}")
    return alerts


if __name__ == '__main__':
    run_real_time_pipeline()