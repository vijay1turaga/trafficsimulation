# PPT Summary: V2X-Predict

## Slide 1: Title
V2X-Predict: Spatiotemporal Traffic Congestion Forecasting using SUMO, NS-3, and V2V Communication

## Slide 2: Objective
- Proactive congestion prediction (not detection)
- Eliminate lag by forecasting before vehicles stop
- Use mobility + network QoS data

## Slide 3: Methodology
- SUMO: Urban traffic simulation (Manhattan grid)
- NS-3: V2V communication (IEEE 802.11p)
- Integration: TraCI Python controller
- AI: Bi-LSTM for spatiotemporal modeling

## Slide 4: Data Collection
- Mobility: Speed, acceleration, position
- QoS: PDR, latency
- Synchronization by timestamps
- High-resolution time-series

## Slide 5: Dataset Engineering
- Preprocessing: Min-Max normalization, noise filtering
- Tensor conversion: (samples, time_steps, features)
- Labeling: 1=congestion, 0=free flow

## Slide 6: AI Model
- Bidirectional LSTM captures forward/backward dependencies
- Trains on fused spatiotemporal + QoS data
- Outputs prediction + confidence score

## Slide 7: Explainable AI
- Feature importance analysis
- Identifies causes: low speed, high latency, low PDR

## Slide 8: V2V Logic
- Vehicles exchange speed, position, QoS
- Range 100-300m, packet loss, delay

## Slide 9: Real-Time Pipeline
1. Generate mobility (SUMO)
2. Generate QoS (NS-3)
3. Fuse data
4. Preprocess
5. Predict with Bi-LSTM
6. Broadcast alerts via V2V

## Slide 10: Results
- Console: Predictions with confidence
- Graphs: Speed vs Time, Latency vs Congestion, PDR vs Density
- Highlight congestion zones in SUMO

## Slide 11: Performance
- Accuracy, Precision/Recall
- Low prediction latency
- PDR impact analysis

## Slide 12: Conclusion
- Ad-hoc vehicular intelligence without RSU
- Lightweight for edge deployment
- Research-level implementation