import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Bidirectional, LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import numpy as np

def build_bilstm_model(input_shape):
    model = Sequential()
    model.add(Bidirectional(LSTM(64, return_sequences=True), input_shape=input_shape))
    model.add(Dropout(0.2))
    model.add(Bidirectional(LSTM(32)))
    model.add(Dropout(0.2))
    model.add(Dense(16, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))  # Binary classification
    
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

def train_model(X_train, y_train, epochs=50, batch_size=32):
    input_shape = (X_train.shape[1], X_train.shape[2])
    model = build_bilstm_model(input_shape)
    
    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    
    history = model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, 
                        validation_split=0.2, callbacks=[early_stop])
    
    model.save('models/bilstm_model.h5')
    return model, history

def predict_congestion(model, X_test):
    predictions = model.predict(X_test)
    confidence = np.max(predictions, axis=1) if len(predictions.shape) > 1 else predictions.flatten()
    return (predictions > 0.5).astype(int), confidence

def explain_predictions(model, X_sample):
    # Simple feature importance using gradients
    X_sample = tf.convert_to_tensor(X_sample, dtype=tf.float32)
    with tf.GradientTape() as tape:
        tape.watch(X_sample)
        predictions = model(X_sample)
    
    gradients = tape.gradient(predictions, X_sample)
    importance = tf.reduce_mean(tf.abs(gradients), axis=0)
    return importance.numpy()

if __name__ == "__main__":
    # Load data
    X = np.load('data/X.npy')
    y = np.load('data/y.npy')
    
    # Train model
    model, history = train_model(X, y)
    print("Model trained and saved.")