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

    MAX_TIME = config["Max_time"]                                                                   # extreme time of simulation (s)

    while traci.simulation.getTime() < MAX_TIME:
        if int(traci.simulation.getTime()) % 2 == 0:                                                # return real time of simulation
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
    veh_type = random.choice(config["vehicles"])                                                   # aleatory vType
    edges = possible_routes(veh_type)

    for travel in range(10):                                                                       # trying up to 10 times.
        from_edge = random.choice(edges)
        to_edge = random.choice(edges)
        color = (random.randint(50, 255),random.randint(50, 255),random.randint(50, 255))

        # Evitar origem = destino
        while to_edge == from_edge:
           to_edge = random.choice(edges)

        route = traci.simulation.findRoute(from_edge, to_edge, vType=veh_type)

        if not route.edges:
            continue                                                                              # try other couple
        
        if route.edges:
            route_id = f"route_{veh_id}"
            traci.route.add(route_id, route.edges)

            traci.vehicle.add(
                vehID=veh_id,
                routeID=route_id,
                typeID=veh_type,
                depart=traci.simulation.getTime()
            )
            
            if veh_type == "bus":
                traci.vehicle.setColor(veh_id, (255, 0, 0))                                     # bus is red
            else:
                traci.vehicle.setColor(
                    veh_id,
                    (random.randint(50,255), random.randint(50,255), random.randint(50,255))
                )

            return                                                                               # success                                                                             

    print(f"⚠️ It was not possible to create a route for {veh_id}")                             # in this case it's not possible to create a route

"""Surch the edges for routes"""
def possible_routes(veh_type):
    valid_edges = []

    for edge in traci.edge.getIDList():

        if edge.startswith(":"):                                                                # ignore internals edges  (cintersections)
            continue
       
        if traci.edge.getLaneNumber(edge) == 0:                                                 # it needs to have at least one lane.
            continue
        
        for i in range(traci.edge.getLaneNumber(edge)):                                         # checks if any lane accepts cars or vehicles.
            lane_id = f"{edge}_{i}"
            allowed = traci.lane.getAllowed(lane_id)
            
            """Verify if the vehicle is permitted"""
            if not allowed:
                if veh_type not in config["RESTRICTED_TYPES"]:
                    valid_edges.append(edge)
                    break

            else:                                                                               # case 2: lane with restriction
                if veh_type in allowed:
                    valid_edges.append(edge)
                    break

    return valid_edges

if __name__ == "__main__":
    main()