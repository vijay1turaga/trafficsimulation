import streamlit as st
import traci
import numpy as np
import tensorflow as tf
import plotly.graph_objects as go
import time
import os

# ---------------------------
# PATHS
# ---------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUMO_CONFIG = os.path.join(BASE_DIR, "sumo_config", "simple.sumocfg")
MODEL_PATH = os.path.join(BASE_DIR, "traffic_model.h5")

model = tf.keras.models.load_model(MODEL_PATH)

st.set_page_config(layout="wide")
st.title("🚦 Smart Traffic Dashboard")

# ---------------------------
# BUTTON
# ---------------------------
if st.button("▶ Start Simulation"):

    traci.start([
        "sumo-gui",
        "-c", SUMO_CONFIG,
        "--start",
        "--delay", "400"   # 🔥 SLOW VEHICLES
    ])

    time.sleep(3)

    last_status = None
    key_steps = []

    correct = 0
    total = 0

    final_data = None

    for step in range(300):

        traci.simulationStep()
        time.sleep(0.15)

        veh_ids = traci.vehicle.getIDList()
        if len(veh_ids) == 0:
            continue

        speeds = [traci.vehicle.getSpeed(v) for v in veh_ids]
        accs = [traci.vehicle.getAcceleration(v) for v in veh_ids]

        avg_speed = np.mean(speeds)
        avg_acc = np.mean(accs)
        veh_count = len(veh_ids)

        # ---------------------------
        # DYNAMIC VALUES (IMPORTANT)
        # ---------------------------
        pdr = np.clip((avg_speed + np.random.uniform(-0.5, 0.5)) / 5, 0, 1)
        latency = np.clip((veh_count + np.random.uniform(-5, 5)) / 50, 0, 1)

        input_data = np.array([[[avg_speed, avg_acc, pdr, latency]]])
        pred = model.predict(input_data, verbose=0)[0][0]

        # ---------------------------
        # STATUS
        # ---------------------------
        if pred > 0.6:
            status = "🚨 High Congestion"
        elif pred > 0.3:
            status = "⚠️ Medium Traffic"
        else:
            status = "✅ Smooth Traffic"

        # ---------------------------
        # STORE ONLY CHANGE STEPS
        # ---------------------------
        if status != last_status:
            key_steps.append({
                "step": step,
                "status": status,
                "speed": avg_speed,
                "pdr": pdr,
                "latency": latency
            })
            last_status = status

        # keep last snapshot
        final_data = (avg_speed, pdr, latency, veh_count, pred)

        # ---------------------------
        # ACCURACY
        # ---------------------------
        actual = 1 if (avg_speed < 2 and veh_count > 20) else 0
        pred_label = 1 if pred > 0.5 else 0

        if pred_label == actual:
            correct += 1
        total += 1

        # STOP AFTER 4 KEY EVENTS
        if len(key_steps) >= 4:
            break

    traci.close()

    accuracy = (correct / total) * 100

    # ---------------------------
    # UI OUTPUT
    # ---------------------------
    st.subheader("📊 Key Traffic Changes (Only Important Steps)")

    for k in key_steps:
        st.success(f"Step {k['step']} → {k['status']}")

    st.metric("🎯 Prediction Accuracy", f"{accuracy:.2f}%")

    # ---------------------------
    # BAR GRAPH (IMPORTANT)
    # ---------------------------
    if final_data:
        avg_speed, pdr, latency, veh_count, pred = final_data

        fig = go.Figure(data=[
            go.Bar(
                x=["Speed", "PDR", "Latency"],
                y=[avg_speed, pdr, latency]
            )
        ])

        st.plotly_chart(fig, use_container_width=True)

    st.info("AI analyzes speed, density & delay to detect congestion.")