import streamlit as st
import traci
import numpy as np
import tensorflow as tf
import plotly.graph_objects as go

# ---------------------------
# CONFIG
# ---------------------------
SUMO_CONFIG = "sumo_config/simple.sumocfg"

# Load model
model = tf.keras.models.load_model("traffic_model.h5")

st.set_page_config(layout="wide")
st.title("🚦 Smart Traffic AI Dashboard (SUMO + Model)")

if st.button("▶ Start Simulation"):

    traci.start([
        "sumo-gui",
        "-c", SUMO_CONFIG,
        "--start"
    ])

    key_steps = []
    last_status = ""

    correct = 0
    total = 0

    for step in range(200):

        traci.simulationStep()

        veh_ids = traci.vehicle.getIDList()

        speeds = [traci.vehicle.getSpeed(v) for v in veh_ids]
        accs = [traci.vehicle.getAcceleration(v) for v in veh_ids]

        avg_speed = np.mean(speeds) if speeds else 0
        avg_acc = np.mean(accs) if accs else 0
        veh_count = len(veh_ids)

        # ---------------------------
        # REALISTIC FEATURES
        # ---------------------------
        pdr = max(0, min(1, avg_speed / 5))
        latency = max(0, min(1, veh_count / 100))

        # ---------------------------
        # MODEL INPUT (MATCH DATASET)
        # ---------------------------
        input_data = np.array([[avg_speed, avg_acc, pdr, latency]])

        prediction = model.predict(input_data, verbose=0)[0][0]

        # ---------------------------
        # STATUS
        # ---------------------------
        if prediction > 0.5:
            status = "High Congestion"
        elif prediction > 0.3:
            status = "Medium Traffic"
        else:
            status = "Smooth Traffic"

        # ---------------------------
        # GROUND TRUTH (for accuracy)
        # ---------------------------
        if avg_speed < 2 and veh_count > 80:
            actual = 1
        else:
            actual = 0

        pred_label = 1 if prediction > 0.5 else 0

        if pred_label == actual:
            correct += 1

        total += 1
        accuracy = correct / total

        # ---------------------------
        # STORE ONLY CHANGE POINTS
        # ---------------------------
        if status != last_status:
            key_steps.append({
                "step": step,
                "speed": round(avg_speed, 2),
                "pdr": round(pdr, 2),
                "latency": round(latency, 2),
                "status": status,
                "accuracy": accuracy
            })
            last_status = status

        if len(key_steps) >= 4:
            break

    traci.close()

    # =========================
    # SHOW RESULTS (SHORT)
    # =========================
    st.subheader("📊 Key Traffic Changes")

    for k in key_steps:
        if k["status"] == "High Congestion":
            st.error(f"Step {k['step']} → 🚨 {k['status']}")
        elif k["status"] == "Medium Traffic":
            st.warning(f"Step {k['step']} → ⚠️ {k['status']}")
        else:
            st.success(f"Step {k['step']} → ✅ {k['status']}")

    # =========================
    # BAR GRAPH
    # =========================
    st.subheader("📊 Performance Metrics")

    labels = [f"S{k['step']}" for k in key_steps]

    fig = go.Figure(data=[
        go.Bar(name="Speed", x=labels, y=[k["speed"] for k in key_steps]),
        go.Bar(name="PDR", x=labels, y=[k["pdr"] for k in key_steps]),
        go.Bar(name="Latency", x=labels, y=[k["latency"] for k in key_steps]),
    ])

    fig.update_layout(barmode='group', template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # =========================
    # ACCURACY
    # =========================
    st.subheader("🎯 Prediction Accuracy")

    for k in key_steps:
        st.write(f"Step {k['step']} → {k['accuracy']*100:.2f}%")

    # =========================
    # FINAL EXPLANATION
    # =========================
    st.subheader("🧠 AI Explanation")

    final = key_steps[-1]

    if final["status"] == "High Congestion":
        st.error("🚨 Heavy traffic due to low speed and high vehicle density.")
    elif final["status"] == "Medium Traffic":
        st.warning("⚠️ Moderate traffic with reduced speed.")
    else:
        st.success("✅ Traffic is smooth with good speed and low density.")