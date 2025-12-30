import traci
from sumolib import checkBinary
import json

RED = [255, 0, 0]
EDGE_ID = 'closed'
VEHICLES = ['1', '4', '8']

sumoBinary = checkBinary('sumo-gui')

# Load config at config\config.json
with open(r'config/config.json', 'r') as config_file:
    config = json.load(config_file)


def main():
    startSim()

    while shouldContinueSim():
        traci.simulationStep()

    traci.close()


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

"""Checks that the simulation should continue running.
   Returns:
   bool: `True` if there are any vehicles on or waiting to enter the network. `False` otherwise.
"""

def shouldContinueSim():
    numVehicles = traci.simulation.getMinExpectedNumber()
    return True if numVehicles > 0 else False

def getOurDeparted(filterIds=[]):
    num_vehicle = traci.vehicle.getIDCount()  # Return a number of vehicles
    IDs_v = traci.vehicle.getIDList()  # Return a tuple with the IDs

    """Returns a set of filtered vehicle IDs that departed onto the network during this simulation step.
    Args:
        filterIds ([String]): The set of vehicle IDs to filter for.
    Returns:
        [String]: A set of vehicle IDs.
    """
    newlyDepartedIds = traci.simulation.getDepartedIDList()

    filteredDepartedIds = newlyDepartedIds if len(
        filterIds) == 0 else set(newlyDepartedIds).intersection(filterIds)
    return filteredDepartedIds

if __name__ == "__main__":
    main()
