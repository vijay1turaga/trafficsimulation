# V2X-Predict: Spatiotemporal Traffic Congestion Forecasting using SUMO, NS-3, and V2V Communication

## Project Overview
This project develops a proactive traffic congestion prediction system using SUMO for traffic simulation, NS-3 for V2V communication, and Bi-LSTM for AI-based forecasting.

## Features
- Realistic urban traffic simulation with Manhattan grid
- V2V communication using IEEE 802.11p
- Cross-layer data fusion (mobility + QoS)
- Bi-LSTM model for spatiotemporal prediction
- Explainable AI with feature importance
- Real-time prediction pipeline
- Visualization and performance metrics

## Requirements
- SUMO (Simulation of Urban Mobility)
- NS-3 (Network Simulator 3)
- Python 3.8+
- TensorFlow or PyTorch
- Required Python packages (see requirements.txt)

## Installation
1. Install SUMO: Follow https://sumo.dlr.de/docs/Installing/index.html
2. Install NS-3: Follow https://www.nsnam.org/docs/release/3.35/tutorial/html/getting-started.html
3. Install Python dependencies: `pip install -r requirements.txt`

## 🚀 New: Project Dashboard
Open `dashboard.html` in your browser for a complete visual overview of the project – live plots, model results, metrics, and controls all in one place!

```
start dashboard.html
```

## Usage
1. Configure SUMO network in `sumo_config/`
2. Run the hybrid ingestion pipeline: `python python_controller/hybrid_bridge.py`
3. Train the Bi-LSTM model: `python python_controller/train_model.py`
4. Run real-time prediction: `python python_controller/predict.py`
5. Optionally run the live simulator with alerts: `python live_simulation.py`
6. Visualize results: `python visualization/plot_graphs.py`

## Project Structure
- `sumo_config/`: SUMO network, routes, and configuration files
- `ns3_scripts/`: NS-3 C++ scripts for VANET simulation
- `python_controller/`: Python scripts for TraCI control, data fusion, and AI model
- `data/`: Datasets and sample data
- `models/`: Trained AI models
- `visualization/`: Scripts for graphs and plots
- `docs/`: Documentation, setup instructions, and PPT summary
- `logs/`: Output logs and results

## Performance Metrics
- Accuracy, Precision, Recall
- Prediction latency
- Packet Delivery Ratio

## License
This project is for educational/research purposes.