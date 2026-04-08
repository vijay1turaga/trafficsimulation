import numpy as np
import tensorflow as tf
from sklearn.metrics import accuracy_score, precision_score, recall_score
from bilstm_model import build_bilstm_model, predict_congestion, explain_predictions
import matplotlib.pyplot as plt

def evaluate_model(model, X_test, y_test):
    y_pred, confidence = predict_congestion(model, X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    
    return accuracy, precision, recall

def plot_feature_importance(model, X_sample):
    importance = explain_predictions(model, X_sample[:1])  # First sample
    features = ['speed', 'acceleration', 'x', 'y', 'pdr', 'latency']
    
    plt.figure(figsize=(10, 6))
    plt.bar(features, importance.mean(axis=0))
    plt.title('Feature Importance for Congestion Prediction')
    plt.xlabel('Features')
    plt.ylabel('Importance')
    plt.savefig('visualization/feature_importance.png')
    plt.show()

def plot_predictions_vs_actual(y_true, y_pred, confidence):
    plt.figure(figsize=(12, 6))
    
    plt.subplot(1, 2, 1)
    plt.plot(y_true[:100], label='Actual')
    plt.plot(y_pred[:100], label='Predicted')
    plt.title('Actual vs Predicted Congestion (First 100 samples)')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(confidence[:100])
    plt.title('Prediction Confidence')
    plt.xlabel('Sample')
    plt.ylabel('Confidence')
    
    plt.tight_layout()
    plt.savefig('visualization/predictions.png')
    plt.show()

if __name__ == "__main__":
    # Load model and data
    model = tf.keras.models.load_model('models/bilstm_model.h5')
    X = np.load('data/X.npy')
    y = np.load('data/y.npy')
    
    # Evaluate
    accuracy, precision, recall = evaluate_model(model, X, y)
    
    # Explain
    plot_feature_importance(model, X)
    
    # Plot predictions
    y_pred, confidence = predict_congestion(model, X)
    plot_predictions_vs_actual(y, y_pred, confidence)