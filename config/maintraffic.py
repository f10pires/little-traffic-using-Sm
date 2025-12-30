import traci
from sumolib import checkBinary

RED = [255, 0, 0]
EDGE_ID = 'closed'
VEHICLES = ['1', '4', '8']

sumoBinary = checkBinary('sumo-gui')


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
            '--net-file', r'C:\Users\felip\OneDrive\Documentos\IC\IC-2\Configuration\little-traffic-using-Sm\config\net.net.xml',
            '--route-files', r'C:\Users\felip\OneDrive\Documentos\IC\IC-2\Configuration\little-traffic-using-Sm\config\routes.trip.xml',
            '--additional-files', r'C:\Users\felip\OneDrive\Documentos\IC\IC-2\Configuration\little-traffic-using-Sm\config\additional.add.xml',
            '--gui-settings-file', r'C:\Users\felip\OneDrive\Documentos\IC\IC-2\Configuration\little-traffic-using-Sm\config\viewssettings.xml',
            '--delay','200',
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
