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

## Usage
1. Configure SUMO network in `sumo_config/`
2. Run NS-3 simulation: `./waf --run vanet_simulation` in `ns3_scripts/`
3. Run Python controller: `python python_controller/traci_controller.py`
4. Train model: `python python_controller/train_model.py`
5. Predict: `python python_controller/predict.py`
6. Visualize: `python visualization/plot_graphs.py`

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