# Architecture Diagram

## High-Level Architecture

```
[SUMO Simulation] --> [TraCI Controller] --> [Data Collection]
       |                       |                       |
       |                       |                       |
[NS-3 V2V Simulation] --> [Data Fusion] --> [Preprocessing]
                                               |
                                               |
                                         [Bi-LSTM Model]
                                               |
                                               |
                                         [Prediction Output]
                                               |
                                               |
                                         [Visualization & Alerts]
```

## Components

1. **SUMO**: Generates realistic traffic mobility data
2. **NS-3**: Simulates V2V communication and QoS metrics
3. **Python Controller**: Integrates simulations, fuses data, runs AI model
4. **Bi-LSTM**: Predicts congestion using spatiotemporal features
5. **Visualization**: Displays results and feature importance

## Data Flow

1. SUMO runs traffic simulation, exports mobility data
2. NS-3 simulates V2V packets, measures PDR and latency
3. Data synchronized by timestamps
4. Preprocessed into 3D tensors
5. Fed into Bi-LSTM for training/prediction
6. Outputs predictions with confidence scores
7. Visualized and logged

## V2V Communication

- Vehicles broadcast speed, position, QoS metrics
- Range: 100-300m
- Protocol: IEEE 802.11p (WAVE)
- Includes packet loss and delay simulation