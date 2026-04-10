import streamlit as st
import traci
import numpy as np
import time
import os
import plotly.graph_objects as go

# ---------------------------
# PATHS
# ---------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUMO_CONFIG = os.path.join(BASE_DIR, "sumo_config", "simple.sumocfg")

st.set_page_config(layout="wide")
st.title("🚦 Traffic Analysis Dashboard")

# ---------------------------
# START BUTTON
# ---------------------------
if st.button("▶ Start Simulation"):

    traci.start([
        "sumo-gui",
        "-c", SUMO_CONFIG,
        "--start",
        "--delay", "400"
    ])

    time.sleep(3)

    steps, speed_hist, latency_hist, pdr_hist = [], [], [], []
    key_steps = []
    last_status = None

    correct = 0
    total = 0

    for step in range(200):

        traci.simulationStep()
        time.sleep(0.15)

        veh_ids = traci.vehicle.getIDList()
        if len(veh_ids) == 0:
            continue

        speeds = [traci.vehicle.getSpeed(v) for v in veh_ids]
        avg_speed = np.mean(speeds)
        veh_count = len(veh_ids)

        latency = np.clip(veh_count / 50, 0, 1)
        pdr = np.clip(avg_speed / 5, 0, 1)

        steps.append(step)
        speed_hist.append(avg_speed)
        latency_hist.append(latency)
        pdr_hist.append(pdr)

        # ---------------------------
        # STATUS + REASON
        # ---------------------------
        if avg_speed < 2 and veh_count > 20:
            status = "Congestion"
            reason = f"Low speed ({avg_speed:.2f}) & high vehicles ({veh_count})"
            color = "red"
            actual = 1
        elif avg_speed < 3:
            status = "Increasing Traffic"
            reason = f"Speed decreasing ({avg_speed:.2f})"
            color = "orange"
            actual = 0
        else:
            status = "No Congestion"
            reason = f"Good speed ({avg_speed:.2f}) & low vehicles ({veh_count})"
            color = "green"
            actual = 0

        # simple prediction rule
        pred_label = 1 if avg_speed < 2.5 else 0

        if pred_label == actual:
            correct += 1
        total += 1

        if status != last_status:
            key_steps.append({
                "step": step,
                "status": status,
                "reason": reason,
                "color": color
            })
            last_status = status

        if len(key_steps) >= 8:
            break

    traci.close()

    accuracy = (correct / total) * 100

    # ---------------------------
    # 🎯 ACCURACY DISPLAY
    # ---------------------------
    st.metric("🎯 Prediction Accuracy", f"{accuracy:.2f}%")

    # ---------------------------
    # 🚦 PAST TRAFFIC CHANGES (6 STEPS)
    # ---------------------------
    st.subheader("📊 Past Traffic Changes (Key Events)")

    key_steps = key_steps[1:7]

    for k in key_steps:
        if k["color"] == "red":
            st.error(f"Step {k['step']} → 🚨 Congestion")
        elif k["color"] == "orange":
            st.warning(f"Step {k['step']} → ⚠️ Increasing Traffic")
        else:
            st.success(f"Step {k['step']} → ✅ No Congestion")

        st.write(f"👉 Reason: {k['reason']}")

    # ---------------------------
    # 🔮 FUTURE PREDICTION
    # ---------------------------
    st.subheader("🔮 Future Prediction")

    last = key_steps[-1]

    for i in range(1, 3):
        future_step = last["step"] + i * 10

        if last["status"] == "Increasing Traffic":
            st.error(f"Step {future_step} → 🚨 Congestion likely")
        elif last["status"] == "No Congestion":
            st.success(f"Step {future_step} → ✅ Traffic remains smooth")
        else:
            st.warning(f"Step {future_step} → ⚠️ Traffic may change")

    # ---------------------------
    # 📊 GRAPHS
    # ---------------------------
    st.subheader("📊 Graphs")

    # Speed Graph
    st.markdown("### 📈 Speed Graph")
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=steps, y=speed_hist))
    st.plotly_chart(fig1, use_container_width=True)

    # Latency Graph
    st.markdown("### ⏱ Latency Graph")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=steps, y=latency_hist))
    st.plotly_chart(fig2, use_container_width=True)

    # Combined Bar Graph
    st.markdown("### 📊 Traffic Reason Analysis")

    fig3 = go.Figure(data=[
        go.Bar(
            x=["Speed", "Latency", "PDR"],
            y=[np.mean(speed_hist), np.mean(latency_hist), np.mean(pdr_hist)]
        )
    ])

    st.plotly_chart(fig3, use_container_width=True)

    st.success("Simulation Completed ✅")