import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Bidirectional, LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
# import shap  # Commented out - not needed for predict_congestion



def build_bilstm_model(input_shape):
    model = Sequential()
    model.add(Bidirectional(LSTM(64, return_sequences=True), input_shape=input_shape))
    model.add(Dropout(0.2))
    model.add(Bidirectional(LSTM(32)))
    model.add(Dropout(0.2))
    model.add(Dense(16, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))

    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model



def train_model(X_train, y_train, X_val, y_val, epochs=50, batch_size=32):
    input_shape = (X_train.shape[1], X_train.shape[2])
    model = build_bilstm_model(input_shape)
    
    # Class weights for imbalance (congestion is rarer)
    from sklearn.utils.class_weight import compute_class_weight
    class_weights = compute_class_weight(
        'balanced', 
        classes=np.unique(y_train), 
        y=y_train
    )
    class_weight_dict = {0: class_weights[0], 1: class_weights[1]}
    print(f"Class weights: {class_weight_dict}")
    
    callbacks = [
        EarlyStopping(monitor='val_accuracy', patience=8, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6)
    ]

    history = model.fit(
        X_train, y_train,
        epochs=epochs,
        batch_size=batch_size,
        validation_data=(X_val, y_val),
        class_weight=class_weight_dict,
        callbacks=callbacks,
        verbose=1
    )

    model.save('models/bilstm_model.h5')
    return model, history




def predict_congestion(model, X_test, temperature=1.5):
    """Temperature scaling for realistic confidence (0.7-0.95 range)"""
    predictions = model.predict(X_test, verbose=0)
    
    # Apply temperature scaling to soften extreme probabilities
    logits = np.log(predictions / (1 - predictions + 1e-8)) / temperature
    calibrated_probs = 1 / (1 + np.exp(-logits))
    
    confidence = calibrated_probs.flatten()
    predictions = (confidence > 0.5).astype(int).flatten()
    
    print(f"Confidence range: {confidence.min():.3f} - {confidence.max():.3f}")
    return predictions, confidence



def explain_predictions(model, X_sample, background=None):
    if background is None:
        background = X_sample[np.random.choice(X_sample.shape[0], min(50, X_sample.shape[0])), :, :]

    try:
        explainer = shap.DeepExplainer(model, background)
    except Exception:
        explainer = shap.GradientExplainer(model, background)

    shap_values = explainer.shap_values(X_sample)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]

    importance = np.mean(np.abs(shap_values), axis=(0, 1))
    return importance


if __name__ == '__main__':
    X = np.load('data/X.npy')
    y = np.load('data/y.npy')
    print(f"Loaded X {X.shape}, y {y.shape}")
