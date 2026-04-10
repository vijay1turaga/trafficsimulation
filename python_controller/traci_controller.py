import os
import csv
import random
import traci

SUMO_BINARY = "C:\\Program Files (x86)\\Eclipse\\Sumo\\bin\\sumo.exe"
SUMO_CONFIG = "sumo_config/manhattan.sumocfg"
MOBILITY_TRACE_PATH = "data/sumo_mobility_trace.csv"
VEHICLE_MAP_PATH = "data/vehicle_node_map.csv"


def ensure_data_dir():
    os.makedirs('data', exist_ok=True)


def save_csv(path, rows, fieldnames):
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_sumo_simulation(scenario='medium', max_steps=1200, step_length=0.1):
    """Run SUMO and create a mobility trace for NS-3 and fusion."""
    ensure_data_dir()

    command = [SUMO_BINARY, '-c', SUMO_CONFIG, '--step-length', str(step_length), '--no-warnings', '--start']
    traci.start(command)

    mobility_rows = []
    vehicle_map = {}
    edges = traci.edge.getIDList()
    injection_rate = {
        'low': 0.01,
        'medium': 0.05,
        'high': 0.12
    }.get(scenario, 0.05)

    random.seed(42)
    step = 0

    while traci.simulation.getMinExpectedNumber() > 0 and step < max_steps:
        traci.simulationStep()
        current_time = round(traci.simulation.getTime(), 3)

        if random.random() < injection_rate and len(edges) >= 2:
            origin = random.choice(edges)
            destination = random.choice(edges)
            if origin != destination:
                try:
                    route_edges = traci.simulation.findRoute(origin, destination).edges
                    if route_edges:
                        route_id = f'route_{step}_{len(vehicle_map)}'
                        veh_id = f'veh_{len(vehicle_map)}'
                        traci.route.add(route_id, route_edges)
                        traci.vehicle.add(veh_id, route_id, depart=str(current_time), typeID='car')
                except Exception:
                    pass

        for veh_id in traci.vehicle.getIDList():
            try:
                speed = traci.vehicle.getSpeed(veh_id)
                accel = traci.vehicle.getAcceleration(veh_id)
                x, y = traci.vehicle.getPosition(veh_id)
                lane = traci.vehicle.getLaneID(veh_id)
                if veh_id not in vehicle_map:
                    vehicle_map[veh_id] = len(vehicle_map)

                mobility_rows.append({
                    'timestamp': current_time,
                    'vehicle_id': veh_id,
                    'source_node': vehicle_map[veh_id],
                    'speed': speed,
                    'acceleration': accel,
                    'x': x,
                    'y': y,
                    'lane': lane
                })
            except Exception:
                continue

        step += 1

    traci.close()

    save_csv(MOBILITY_TRACE_PATH, mobility_rows,
             ['timestamp', 'vehicle_id', 'source_node', 'speed', 'acceleration', 'x', 'y', 'lane'])
    save_csv(VEHICLE_MAP_PATH,
             [{'vehicle_id': vid, 'source_node': idx} for vid, idx in vehicle_map.items()],
             ['vehicle_id', 'source_node'])

    print(f"SUMO mobility trace collected: {len(mobility_rows)} rows, {len(vehicle_map)} unique vehicles")
    print(f"Saved mobility trace: {MOBILITY_TRACE_PATH}")
    print(f"Saved vehicle-node mapping: {VEHICLE_MAP_PATH}")

    return MOBILITY_TRACE_PATH, VEHICLE_MAP_PATH


if __name__ == '__main__':
    run_sumo_simulation()
