import traci
import sumolib
import time
import csv
from datetime import datetime

def run_sumo_simulation():
    # Start SUMO with TraCI
    sumoBinary = "C:\\Program Files (x86)\\Eclipse\\Sumo\\bin\\sumo.exe"
    traci.start([sumoBinary, "-c", "sumo_config/manhattan.sumocfg", "--step-length", "0.1"])

    # Data collection
    mobility_data = []
    step = 0
    while traci.simulation.getMinExpectedNumber() > 0 and step < 36000:  # 1 hour simulation
        traci.simulationStep()
        vehicles = traci.vehicle.getIDList()
        timestamp = traci.simulation.getTime()
        for veh_id in vehicles:
            speed = traci.vehicle.getSpeed(veh_id)
            accel = traci.vehicle.getAcceleration(veh_id)
            x, y = traci.vehicle.getPosition(veh_id)
            mobility_data.append({
                'timestamp': timestamp,
                'vehicle_id': veh_id,
                'speed': speed,
                'acceleration': accel,
                'x': x,
                'y': y
            })
        step += 1

    traci.close()

    # Save mobility data
    with open('data/mobility_data.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'vehicle_id', 'speed', 'acceleration', 'x', 'y'])
        writer.writeheader()
        writer.writerows(mobility_data)

    print("Mobility data collected and saved.")

if __name__ == "__main__":
    run_sumo_simulation()