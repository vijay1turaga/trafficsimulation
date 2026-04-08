import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os

def load_data():
    # Load sample fused data
    df = pd.read_csv('data/sample_dataset.csv')
    return df, None  # No separate QoS, already fused

def synchronize_data(df, qos_df):
    # Data is already synchronized in sample dataset
    return df

def preprocess_data(df):
    # Min-Max normalization
    scaler = MinMaxScaler()
    features = ['speed', 'acceleration', 'x', 'y', 'pdr', 'latency']
    df[features] = scaler.fit_transform(df[features])
    
    # Noise filtering (simple moving average)
    df[features] = df[features].rolling(window=5, min_periods=1).mean()
    
    # Label congestion (speed < 5 m/s as congestion)
    df['congestion'] = (df['speed'] < 0.1).astype(int)  # After normalization, low speed
    
    return df, scaler

def create_tensors(df, time_steps=5):
    features = ['speed', 'acceleration', 'x', 'y', 'pdr', 'latency']
    data = df[features].values
    labels = df['congestion'].values
    
    X, y = [], []
    for i in range(len(data) - time_steps):
        X.append(data[i:i+time_steps])
        y.append(labels[i+time_steps])
    
    return np.array(X), np.array(y)

if __name__ == "__main__":
    df, _ = load_data()
    fused_df = synchronize_data(df, None)
    processed_df, scaler = preprocess_data(fused_df)
    X, y = create_tensors(processed_df)
    
    # Save processed data
    np.save('data/X.npy', X)
    np.save('data/y.npy', y)
    
    print("Data fusion and preprocessing completed.")