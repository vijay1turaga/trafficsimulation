import streamlit as st
import traci
import pandas as pd
import time

SUMO_CONFIG = "sumo_config/simple.sumocfg"

def start_sumo():
    traci.start([
        "sumo-gui",
        "-c", SUMO_CONFIG,
        "--start"
    ])

st.set_page_config(layout="wide")

st.title("🚦 Live Traffic Simulation (SUMO + AI)")

if st.button("▶ Start Simulation"):

    start_sumo()

    col1, col2, col3 = st.columns(3)

    step_box = st.empty()
    vehicle_box = col1.empty()
    speed_box = col2.empty()
    status_box = col3.empty()
    explanation = st.empty()

    # ✅ GRAPH INIT (IMPORTANT)
    chart = st.line_chart(pd.DataFrame({
        "Vehicles": [],
        "Speed": []
    }))

    for step in range(100):

        try:
            traci.simulationStep()

            vehicles = traci.vehicle.getIDList()

            speed = 50
            if len(vehicles) > 0:
                speed = sum([traci.vehicle.getSpeed(v) for v in vehicles]) / len(vehicles)

            density = len(vehicles)

            # UI
            step_box.markdown(f"### Step: {step}")
            vehicle_box.metric("🚗 Vehicles", density)
            speed_box.metric("⚡ Avg Speed", round(speed, 2))

            # ✅ CORRECT CONGESTION LOGIC
            if density > 50 and speed < 5:
                status_box.error("🚨 High Congestion")
                explanation.markdown("Heavy traffic: too many vehicles and very low speed.")

            elif density > 30 and speed < 8:
                status_box.warning("⚠️ Medium Traffic")
                explanation.markdown("Moderate traffic: vehicles increasing and speed reducing.")

            else:
                status_box.success("✅ Smooth Traffic")
                explanation.markdown("Traffic is smooth: low vehicles and good speed.")

            # ✅ GRAPH UPDATE (FIXED METHOD)
            chart.add_rows(pd.DataFrame({
                "Vehicles": [density],
                "Speed": [speed]
            }))

            time.sleep(0.05)

        except:
            st.warning("Simulation stopped")
            break

    if traci.isLoaded():
        traci.close()

    st.success("Simulation Completed")