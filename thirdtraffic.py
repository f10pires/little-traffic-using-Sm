import traci
from sumolib import checkBinary
import json
import random
from pathlib import Path
import csv
import subprocess
import sys
from sumolib.net import readNet

sumoBinary = checkBinary('sumo-gui')

"""Load config at config\config.json"""
with open(r'config/config.json', 'r') as config_file:
    config = json.load(config_file)

def main():
    """initial functions"""
    init_csv()
    generate_random_trips()
    startSim()

    """Variables"""
    MAX_TIME = config["Max_time"]                                                                   # extreme time of simulation (s)
    time = random.randint(0, MAX_TIME)
    
    print("O veículo aparecerá no tempo de simulação:",time)

    """Simularion"""
    while traci.simulation.getTime() != MAX_TIME:
        if traci.simulation.getTime() == time :
            route_id = addRandomVehicle("MAIN")
            traci.vehicle.setParameter("MAIN", "has.battery.device", "true")
            
        if  "MAIN" in traci.vehicle.getIDList() :
            register("MAIN", traci.simulation.getTime(),"evehicle",route_id)  

        traci.simulationStep()

    traci.close()

"Register informations about vehicle"
def init_csv():
    base_dir = Path(__file__).resolve().parent
    pasta_storing = base_dir / "storing"
    pasta_storing.mkdir(parents=True, exist_ok=True)

    arquivo_csv = pasta_storing / "vehicles.csv"

    """clear vehicles.csv"""
    with open(arquivo_csv, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["== ID ==",
                         "== Atual route ==",
                         "== Distance traveled(m) ==",
                         "== Destination ==",
                         "== Distance from destination(m) ==",
                         "== TYPE ==",
                         "== Batery level ==",
                         "== timestamp =="]) 
    return

"""Run randomTrips.py script"""
def generate_random_trips():
    """Command that replaces terminal execution"""
    cmd = [
        sys.executable,                                                                             # Python executable from the virtual environment (.venv)
        config["random-trip"],
        "-n", config["net-file"],
        "-o", config["trips-file"],
        "-r",  config["route-files"],
        "-e", "500",
        "--period", config["period"],
        "--seed", "42"
    ]

    subprocess.run(cmd, check=True)

"""Starts the simulation."""
def startSim():
    traci.start(
        [
            sumoBinary,
            '--net-file', config["net-file"],
            '--route-files', config["route-files"],
            '--additional-files', config["additional-files"],
            '--gui-settings-file', config["gui-settings-file"],
            '--delay', config["delay"],
            '--start'
        ]
    )

"""Create a vehicle with origin and destinetion """
def addRandomVehicle(veh_id):

    veh_type = "evehicle"                                                   
    edges = possible_routes(veh_type)

    for travel in range(10):                                                                       # trying up to 10 times.
        from_edge = random.choice(edges)
        to_edge = random.choice(edges)
        color = (255,0,0)

        while to_edge == from_edge:                                                                # Avoid origin = destination
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

            parkingID = random.choice(traci.parkingarea.getIDList())
            traci.vehicle.setColor(veh_id, color)

            if parkingIsOnRoute(route.edges, parkingID):
                traci.vehicle.setParkingAreaStop(veh_id, parkingID, 20)
                color = (255,255,255)                                                            # The vehicle that stop in parking is white
                traci.vehicle.setColor(veh_id, color)

        return  route_id                                                                         # success                                                                             

    print(f"⚠️ It was not possible to create a route for {veh_id}")                             # in this case it is not possible to create a route

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

"""Verify if there is parking on route"""
def parkingIsOnRoute(route_edges, parkingID):
    lane_id = traci.parkingarea.getLaneID(parkingID)
    edge_id = lane_id.split("_")[0]
    return edge_id in route_edges

def register(ID, TIME, TYPE, ID_ROUTE):
    base_dir = Path(__file__).resolve().parent
    pasta_storing = base_dir / "storing"
    pasta_storing.mkdir(parents=True, exist_ok=True)

    arquivo_csv = pasta_storing / "vehicles.csv"

    veh_id = ID
    road_id = traci.vehicle.getRoadID(veh_id)

    """ Ignore internal edges (junctions) """
    if road_id.startswith(":"):
        return

    """Get final edge from route"""
    route_edges = traci.route.getEdges(ID_ROUTE)
    destination = route_edges[-1]

    dist = traci.vehicle.getDrivingDistance(
        vehID=veh_id,
        edgeID=destination,
        pos=traci.lane.getLength(f"{destination}_0")
    )


    print("charge:",
        traci.vehicle.getParameter("MAIN",
        "device.battery.actualBatteryCapacity"))
    
    print("electricity:",
      traci.vehicle.getElectricityConsumption("MAIN"))
    
    """Eletric informations"""
    #charge = traci.vehicle.getParameter(ID,"device.battery.chargeLevel")
    #print(charge)

    """Write data to CSV"""
    with open(arquivo_csv, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            veh_id,
            road_id,
            "{:.1f}".format(traci.vehicle.getDistance(veh_id)),
            destination,
            "{:.1f}".format(dist),
            TYPE,
            TIME
            
        ])

if __name__ == "__main__":
    main()