import numpy as np
import tensorflow as tf
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix, roc_auc_score, classification_report
from sklearn.metrics import ConfusionMatrixDisplay
import matplotlib.pyplot as plt
from python_controller.bilstm_model import predict_congestion, explain_predictions


def evaluate_model(model, X_test, y_test):
    y_pred, confidence = predict_congestion(model, X_test)

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)

    try:
        roc_auc = roc_auc_score(y_test, confidence)
    except Exception:
        roc_auc = float('nan')

    print("Evaluation results:")
    print(f"  Accuracy: {accuracy:.4f}")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall: {recall:.4f}")
    print(f"  ROC-AUC: {roc_auc:.4f}")
    print("\nClassification report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'roc_auc': roc_auc,
        'confusion_matrix': cm,
        'y_pred': y_pred,
        'confidence': confidence
    }


def plot_confusion_matrix(cm, labels=['free', 'congested']):
    plt.figure(figsize=(6, 5))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(cmap=plt.cm.Blues, colorbar=False)
    plt.title('Confusion Matrix')
    plt.savefig('visualization/confusion_matrix.png')
    plt.close()



def plot_feature_importance(model, X_sample):
    importance = explain_predictions(model, X_sample[:min(50, len(X_sample))])
    features = ['speed', 'acceleration', 'x', 'y', 'pdr', 'latency']
    
    # Normalize to percentages
    importance_pct = 100 * importance / np.sum(importance)
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(features, importance_pct, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3'])
    plt.title('Feature Importance for Congestion Prediction (%)', fontsize=16, fontweight='bold')
    plt.ylabel('Importance (%)')
    plt.xlabel('Features')
    
    # Add value labels on bars
    for bar, pct in zip(bars, importance_pct.round(1)):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                f'{pct}%', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('visualization/feature_importance.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Top features:", list(zip(features, importance_pct.round(1))))
    return dict(zip(features, importance_pct))



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
    plt.close()


if __name__ == '__main__':
    model = tf.keras.models.load_model('models/bilstm_model.h5')
    X_test = np.load('data/X_test.npy')
    y_test = np.load('data/y_test.npy')

    results = evaluate_model(model, X_test, y_test)
    plot_confusion_matrix(results['confusion_matrix'])
    plot_feature_importance(model, X_test)
    plot_predictions_vs_actual(y_test, results['y_pred'], results['confidence'])
