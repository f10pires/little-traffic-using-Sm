import traci
from sumolib import checkBinary
import json
import random

sumoBinary = checkBinary('sumo-gui')

"""Load config at config\config.json"""
with open(r'config/config.json', 'r') as config_file:
    config = json.load(config_file)

def main():
    startSim()

    veh_counter = 0                                                                                 # vehicle counter
    random.seed(1)                                                                                  # reproduction

    MAX_TIME = config["Max_time"]                                                                   # Extreme time of simulation (s)

    while traci.simulation.getTime() < MAX_TIME:
        if int(traci.simulation.getTime()) % 2 == 0:                                                #return real time of simulation
            addRandomVehicle(f"veh_{veh_counter}")
            veh_counter += 1

        traci.simulationStep()

    traci.close()

"""Starts the simulation."""
def startSim():
    traci.start(
        [
            sumoBinary,
            '--net-file', config["net-file"],
            '--additional-files', config["additional-files"],
            '--gui-settings-file', config["gui-settings-file"],
            '--delay', config["delay"],
            '--start'
        ]
    )

"""Create a vehicle with origin and destinetion """
def addRandomVehicle(veh_id):
    edges = possible_routes()

    for travel in range(10):                                                                       # trying up to 10 times.
        from_edge = random.choice(edges)
        to_edge = random.choice(edges)
        
        # Evitar origem = destino
        while to_edge == from_edge:
           to_edge = random.choice(edges)

        route = traci.simulation.findRoute(from_edge, to_edge)

        if not route.edges:
            continue                                                                              # try other couple
        
        if route.edges:
            route_id = f"route_{veh_id}"
            traci.route.add(route_id, route.edges)

            traci.vehicle.add(
                vehID=veh_id,
                routeID=route_id,
                depart=traci.simulation.getTime()
            )
            return                                                                              # success

    print(f"⚠️ It was not possible to create a route for {veh_id}")                             # In this case it's not possible to create a route

"""Surch the edges for routes"""
def possible_routes():
    valid_edges = []

    for edge in traci.edge.getIDList():

        
        if edge.startswith(":"):                                                                # ignore internals edges  (cintersections)
            continue

       
        if traci.edge.getLaneNumber(edge) == 0:                                                  # It needs to have at least one lane.
            continue
        
        for i in range(traci.edge.getLaneNumber(edge)):                                         # checks if any lane accepts cars or vehicles.
            lane_id = f"{edge}_{i}"
            allowed = traci.lane.getAllowed(lane_id)

           
            if not allowed or "passenger" in allowed:                                            # empty = all allowed
                valid_edges.append(edge)
                break

    return valid_edges

if __name__ == "__main__":
    main()
