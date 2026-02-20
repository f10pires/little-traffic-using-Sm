import traci
from sumolib import checkBinary
import json
import random
from pathlib import Path
import csv
import subprocess
import sys

sumoBinary = checkBinary('sumo-gui')

"""Load config at config/config.json"""
with open(r'config/config.json', 'r') as config_file:
    config = json.load(config_file)

def main():
    """initial functions"""
    function_initializer()
    
    """Simulation"""
    simulation()

def function_initializer():
    setup_results_and_headers()
    generate_random_trips()
    startSim()
    return


def setup_results_and_headers():

    list_vehicles = [f"veh_{i}" for i in range(config["vehicles_number"])]

    base_dir = Path(__file__).resolve().parent
    pasta_results = base_dir / "results"
    
    if not pasta_results.exists():
        pasta_results.mkdir(parents=True, exist_ok=True)
    else:
        for item in pasta_results.iterdir():

            if item.is_file():
                item.unlink()

    cabecalho = [
        "== ID ==",
        "== Velocity (Kh/h) ==",
        "== Atual route ==",
        "== Distance traveled(m) ==",
        "== Destination ==",
        "== Distance from destination(m) ==",
        "== TYPE ==",
        "== Batery level(%) ==",
        "== timestamp =="
    ]

    for veiculo_id in list_vehicles:
        arquivo_csv = pasta_results / f"{veiculo_id}.csv"
        
        with open(arquivo_csv, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(cabecalho)
            

"""Run randomTrips.py script"""
def generate_random_trips():
    cmd = [
        sys.executable,
        config["random-trip"],
        "-n", config["net-file"],
        "-o", config["trips-file"],
        "-r", config["route-files"],
        "-e", "500",
        "-t", 'type="frota_mista"',
        "-a", config["additional-files"],
        "--additional-files", config["additional-random"], 
        "--period", config["period"],
        "--seed", "42",
        "--validate"
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
            '--step-length', config["step"], 
            '--delay', config["delay"],
            '--statistic-output', config["statistic-output"],
            '--duration-log.statistics', 'true',
            '--tripinfo-output', config["tripinfo-output"],
            '--gui-settings-file', config["gui-settings-file"],
            '--start',      
            '--quit-on-end' 
        ]
    )

def simulation():
    """Variables"""
    MAX_TIME = config["Max_time"] 
    vehicles_programming = {} 
    all_vehicles = []
    set_battery_vehicles =[]
    vehicles_that_return = {}


    for id_provisional in range(config["vehicles_number"]): #adiciona o numero de veículos solicitados
        time = random.randint(0, MAX_TIME)
        veh_id = f"veh_{id_provisional}"
        if time not in vehicles_programming: 
            vehicles_programming[time] = []
        vehicles_programming[time].append(veh_id)
        all_vehicles.append(veh_id)
        set_battery_vehicles.append(veh_id)

    while traci.simulation.getTime() != MAX_TIME:
        actual_time = int(traci.simulation.getTime()) #parte inteira do tempo atual
        
        if actual_time in vehicles_programming:
            for vid in vehicles_programming[actual_time]:
                addRandomVehicle(vid)
                print(f"Veículo {vid} aparecerá no tempo {actual_time}")    
            del vehicles_programming[actual_time]

        for active_vid in all_vehicles :
            if active_vid in traci.vehicle.getIDList():
                v_type = traci.vehicle.getTypeID(active_vid)
                r_id = traci.vehicle.getRouteID(active_vid)
                vehicles_that_return = register(active_vid, traci.simulation.getTime(), v_type, r_id,vehicles_that_return)

        traci.simulationStep()
        
        for change_battery in set_battery_vehicles[:] : 
            if change_battery in traci.vehicle.getIDList():
                
                route_id = traci.vehicle.getRouteID(change_battery)
                capacity = float(traci.vehicle.getParameter(change_battery, "device.battery.capacity"))
                current_charge = float(traci.vehicle.getParameter(change_battery, "device.battery.chargeLevel"))
                    
                NEWcurrent_charge = set_baterychargelevel(change_battery, current_charge)
    
                if level_charge(NEWcurrent_charge,capacity) < 25:
                    Olddestination = recharge_substation(change_battery, route_id)
                    vehicles_that_return[change_battery] = Olddestination
       
                set_battery_vehicles.remove(change_battery)
        
        for veh in list(vehicles_that_return.keys()):  
                    destino_original, id_estacao, ja_carregou = vehicles_that_return[veh]

                    if (veh not in traci.chargingstation.getVehicleIDs(id_estacao)) and ja_carregou:

                        traci.vehicle.changeTarget(veh, destino_original)
                        del vehicles_that_return[veh]
                        print(f"Veículo {veh} carregado. Retornando para {destino_original}")
                
        if actual_time > MAX_TIME:
            break
    traci.close()

"""Create a vehicle with origin and destination """
def addRandomVehicle(veh_id):
    veh_type = random.choice(config["vehicles"])                                            
    edges = possible_routes(veh_type)
    route_id = f"route_{veh_id}"

    for travel in range(10): 
        from_edge = random.choice(edges)
        to_edge = random.choice(edges)

        while to_edge == from_edge: 
           to_edge = random.choice(edges)

        route = traci.simulation.findRoute(from_edge, to_edge, vType=veh_type)

        if not route.edges:
            continue 

        if route_id not in traci.route.getIDList():
            traci.route.add(route_id, route.edges)
        
        if veh_id not in traci.vehicle.getIDList():
            traci.vehicle.add(
                vehID=veh_id,
                routeID=route_id,
                typeID=veh_type,
                depart=traci.simulation.getTime()
            )

        if veh_type in ["bus","ElectricBus"]:
            
            if traci.busstop.getIDList() :
                stop_id = random.choice(traci.busstop.getIDList())
                if busStopIsOnRoute(route.edges, stop_id):
                    traci.vehicle.setBusStop(veh_id, stop_id, duration=10)

        else:
            all_parkings = traci.parkingarea.getIDList()
            if all_parkings:
                parkingID = random.choice(all_parkings)

                if parkingIsOnRoute(route.edges, parkingID):
                    traci.vehicle.setParkingAreaStop(veh_id, parkingID, duration=10)

        return route_id, veh_type 

    print(f"It was not possible to create a route for {veh_id}")
    return None, None 

"""Surch the edges for routes"""
def possible_routes(veh_type):
    valid_edges = []
    for edge in traci.edge.getIDList():
        if edge.startswith(":"): # ignore internals edges
            continue
        if traci.edge.getLaneNumber(edge) == 0: 
            continue
        
        for i in range(traci.edge.getLaneNumber(edge)): 
            lane_id = f"{edge}_{i}"
            allowed = traci.lane.getAllowed(lane_id)
            
            if not allowed:
                if veh_type not in config.get("RESTRICTED_TYPES", []):
                    valid_edges.append(edge)
                    break
            else: 
                if veh_type in allowed:
                    valid_edges.append(edge)
                    break
    return valid_edges

"""Verify if there is parking on route"""
def parkingIsOnRoute(route_edges, parkingID):
    lane_id = traci.parkingarea.getLaneID(parkingID)
    edge_id = lane_id.split("_")[0]
    return edge_id in route_edges

def register(veh_id, TIME, TYPE, ID_ROUTE,VTR):
    base_dir = Path(__file__).resolve().parent
    arquivo_csv = base_dir / "results" / f"{veh_id}.csv"

    road_id = traci.vehicle.getRoadID(veh_id)
    if road_id.startswith(":"):
        return VTR

    
    route_edges = traci.route.getEdges(ID_ROUTE)
    destination = route_edges[-1]

    dist = traci.vehicle.getDrivingDistance(
        vehID=veh_id,
        edgeID=destination,
        pos=traci.lane.getLength(f"{destination}_0")
    )

    v_kmh = traci.vehicle.getSpeed(veh_id) * 3.6

    eletric_informations = {
        "electricity": traci.vehicle.getElectricityConsumption(veh_id),
        "capacity": float(traci.vehicle.getParameter(veh_id, "device.battery.capacity")),
        "currentCharge": float(traci.vehicle.getParameter(veh_id, "device.battery.chargeLevel"))
    }                                           

    eletric_informations["stateOfCharge"] = level_charge(eletric_informations["currentCharge"],eletric_informations["capacity"])


    """Logic for change color based in legel charge"""
    cor_level = get_color_by_battery(eletric_informations["stateOfCharge"])
    traci.vehicle.setColor(veh_id, cor_level)
     
    with open(arquivo_csv, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            veh_id,
            "{:.1f}".format(v_kmh),
            road_id,
            "{:.1f}".format(traci.vehicle.getDistance(veh_id)),
            destination,
            "{:.1f}".format(dist),
            TYPE,
            "{:.1f}".format(eletric_informations["stateOfCharge"]),
            TIME       
        ]) 

    """parking logic"""
    for PARKING in traci.parkingarea.getIDList():
        veiculos_estacionados = traci.parkingarea.getVehicleIDs(PARKING)
        for VID in veiculos_estacionados:
            print(f"veículo {VID} estacionado em {PARKING}")
    
    """charging station logic"""
    for STATION in traci.chargingstation.getIDList():
        veiculos_carregando = traci.chargingstation.getVehicleIDs(STATION)
        for VID in veiculos_carregando:
            print(f"veículo {VID} na estação de carregamento {STATION}")
            if VID in VTR : 
                VTR[VID][2] = True
    
    return VTR

def set_baterychargelevel(veh_id, batery):
    new_charge = random.uniform(0, float(batery))
    traci.vehicle.setParameter(veh_id, "device.battery.chargeLevel", str(new_charge))
    return float(traci.vehicle.getParameter(veh_id, "device.battery.chargeLevel"))
    
def level_charge(actual_batery, maximum_batery):
    return (float(actual_batery)*100)/float(maximum_batery)

def recharge_substation(veh_id, route_id):
    route_edges = traci.route.getEdges(route_id)
    destination = route_edges[-1]

    charging_stations = traci.chargingstation.getIDList()
    if not charging_stations:
        return
    
    station_id = random.choice(charging_stations)
    lane_id = traci.chargingstation.getLaneID(station_id)
    edge_id = lane_id.split("_")[0]

    traci.vehicle.changeTarget(veh_id, edge_id)
    traci.vehicle.setChargingStationStop(veh_id, station_id, duration=100,flags=1)

    return [destination,station_id,False]

def busStopIsOnRoute(route_edges, busStopID):
    lane_id = traci.busstop.getLaneID(busStopID)
    edge_id = lane_id.split("_")[0]
    return edge_id in route_edges

def get_color_by_battery(percentage):      
    if percentage <= 14:
        return (255, 0, 0, 255)      # Vermelho Crítico
    elif percentage <= 28:
        return (255, 69, 0, 255)     # Laranja Avermelhado
    elif percentage <= 42:
        return (255, 165, 0, 255)    # Laranja (Alerta)
    elif percentage <= 56:
        return (255, 255, 0, 255)    # Amarelo (Intermediário)
    elif percentage <= 70:
        return (173, 255, 47, 255)    # Verde Amarelado
    elif percentage <= 85:
        return (127, 255, 0, 255)    # Verde Claro
    else:
        return (0, 255, 0, 255)      # Verde (Cheio)
    
if __name__ == "__main__":
    main()