import traci
from sumolib import checkBinary
import json
import random
from pathlib import Path
import csv

sumoBinary = checkBinary('sumo-gui')

"""Load config at config\config.json"""
with open(r'config/config.json', 'r') as config_file:
    config = json.load(config_file)

def main():
    init_csv()
    startSim()

    "Variables"
    veh_counter = 0                                                                                 # vehicle counter
    random.seed(42)                                                                                 # reproduction

    MAX_TIME = config["Max_time"]                                                                   # extreme time of simulation (s)

    bus_stop = traci.busstop.getIDList()                                                            # bus stops id
    parking = traci.parkingarea.getIDList()

    VehicleWR = select_vehicle(MAX_TIME)                                                           # Vehicle identification that will be recorded in the log. 

    """Simularion"""
    while traci.simulation.getTime() < MAX_TIME:
        if int(traci.simulation.getTime()) % 2 == 0:                                                # return real time of simulation
            type = addRandomVehicle(f"veh_{veh_counter}",bus_stop,parking)
            veh_counter += 1

        traci.simulationStep()

        if f"veh_{VehicleWR}" in traci.vehicle.getIDList():
            register(VehicleWR,traci.simulation.getTime(),traci.vehicle.getTypeID(f"veh_{VehicleWR}"))

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
def addRandomVehicle(veh_id,bus_stop,parking):

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

                stop_id = random.choice(bus_stop)
                
                if busStopIsOnRoute(route.edges, stop_id):
                    traci.vehicle.setBusStop(veh_id, stop_id, 10)
            else:
                parkingID = random.choice(parking)
                traci.vehicle.setColor(veh_id, color)

                if parkingIsOnRoute(route.edges, parkingID):
                    traci.vehicle.setParkingAreaStop(veh_id, parkingID, 20)
                    color = (255,255,255)                                                       # The vehicle that stop in parking is white
                    traci.vehicle.setColor(veh_id, color)

        return veh_type                                                                                   # success                                                                             

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

"""Verify if bus stos is on route"""
def busStopIsOnRoute(route_edges, busStopID):

    lane_id = traci.busstop.getLaneID(busStopID)
    edge_id = lane_id.split("_")[0]

    return edge_id in route_edges

"""Verify if there is parking on route"""
def parkingIsOnRoute(route_edges, parkingID):
    lane_id = traci.parkingarea.getLaneID(parkingID)
    edge_id = lane_id.split("_")[0]
    return edge_id in route_edges

"""Select aleatory ID"""
def select_vehicle(MAX_TIME):
    IDnumbers = []
    for i in range(int(MAX_TIME/2)):
        IDnumbers.append(i)
    return random.choice(IDnumbers)

"Register informations about vehicle"
def init_csv():
    base_dir = Path(__file__).resolve().parent
    pasta_storing = base_dir / "storing"
    pasta_storing.mkdir(parents=True, exist_ok=True)

    arquivo_csv = pasta_storing / "vehicles.csv"

    """clear vegicles.csv"""
    with open(arquivo_csv, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ID","Atual route","TYPE", "timestamp"]) 
    return

def register(ID, TIME,TYPE):
    base_dir = Path(__file__).resolve().parent
    pasta_storing = base_dir / "storing"
    pasta_storing.mkdir(parents=True, exist_ok=True)

    arquivo_csv = pasta_storing / "vehicles.csv"

    veh_id = f"veh_{ID}"

    if veh_id not in traci.vehicle.getIDList():
        return

    road_id = traci.vehicle.getRoadID(veh_id)

    """"ignore internal edges"""
    if road_id.startswith(":"):
        return

    with open(arquivo_csv, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([ID, road_id,TYPE, TIME])

if __name__ == "__main__":
    main()