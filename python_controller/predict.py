import os
import subprocess
import time
import numpy as np
from bilstm_model import build_bilstm_model, predict_congestion
import tensorflow as tf
import traci
import sumolib

def run_real_time_pipeline():
    # Load trained model
    model = tf.keras.models.load_model('../models/bilstm_model.h5')
    
    # Load sample data for demonstration
    X = np.load('../data/X.npy')
    
    # Predict on sample data
    for i in range(min(5, len(X))):  # Predict on first 5 samples
        pred, conf = predict_congestion(model, X[i:i+1])
        print(f"Sample {i}: Congestion predicted: {pred[0]}, Confidence: {conf[0]:.2f}")
        if pred[0] == 1:
            print("Alert broadcasted to nearby vehicles")
        else:
            print("Free flow")

if __name__ == "__main__":
    run_real_time_pipeline()