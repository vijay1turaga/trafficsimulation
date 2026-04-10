import os
import numpy as np
from sklearn.model_selection import train_test_split
import joblib
from python_controller.bilstm_model import train_model
from python_controller.data_fusion import build_fused_dataset

MODEL_DIR = 'models'
SCALER_PATH = os.path.join(MODEL_DIR, 'scaler.save')


def ensure_dirs():
    os.makedirs(MODEL_DIR, exist_ok=True)


def split_dataset(X, y, test_size=0.2, val_size=0.1):
    if len(np.unique(y)) > 1:
        stratify = y
    else:
        stratify = None

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=test_size + val_size, random_state=42, stratify=stratify
    )

    if len(np.unique(y_temp)) > 1:
        stratify_temp = y_temp
    else:
        stratify_temp = None

    val_ratio = val_size / (test_size + val_size)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp,
        test_size=val_ratio,
        random_state=42,
        stratify=stratify_temp
    )

    return X_train, X_val, X_test, y_train, y_val, y_test


def save_scaler(scaler):
    joblib.dump(scaler, SCALER_PATH)
    print(f"Saved scaler: {SCALER_PATH}")


def train_pipeline():
    ensure_dirs()
    fused_df, X, y, scaler = build_fused_dataset()
    save_scaler(scaler)

    X_train, X_val, X_test, y_train, y_val, y_test = split_dataset(X, y)
    model, history = train_model(X_train, y_train, X_val, y_val)

    np.save('data/X_train.npy', X_train)
    np.save('data/X_val.npy', X_val)
    np.save('data/X_test.npy', X_test)
    np.save('data/y_train.npy', y_train)
    np.save('data/y_val.npy', y_val)
    np.save('data/y_test.npy', y_test)

    print('Training complete:')
    print(f'  Train samples: {X_train.shape[0]}')
    print(f'  Validation samples: {X_val.shape[0]}')
    print(f'  Test samples: {X_test.shape[0]}')
    print('  Model saved: models/bilstm_model.h5')

    return model, history, X_test, y_test


if __name__ == '__main__':
    train_pipeline()
