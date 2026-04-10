import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path

# Sample feature data matching [speed, accel, x, y, pdr, latency]
# Generate 100 samples with realistic range
np.random.seed(42)
speed = np.random.normal(8, 3, 100)
accel = np.random.normal(0, 1, 100)
x = np.random.normal(500, 200, 100)
y = np.random.normal(500, 200, 100)
pdr = np.random.normal(0.95, 0.05, 100)
latency = np.random.normal(0.1, 0.05, 100)

X_sample = np.column_stack([speed, accel, x, y, pdr, latency])

scaler = StandardScaler()
scaler.fit(X_sample)

# Save
Path('models').mkdir(exist_ok=True)
joblib.dump(scaler, 'models/scaler.save')
print("Dummy scaler.save created successfully.")
