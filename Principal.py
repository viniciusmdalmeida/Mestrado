from Interface.Simulation import Simulation
from AlgorithmsSensors.cam.Vision_RGB_Depth import *
from AlgorithmsSensors.cam.Vision_RGB import *
from AlgorithmsSensors.lidar.LidarBase import *
from AlgorithmsSensors.IMU.InertialSensors import *

routePoints = [[0,-15,-10,2],[0,-15,-10,2],[50,-15,-10,2]]
algorithm = {"lidar":LidarBase,'IMU':InertialSensorsPrint}

#Start simples
print("Iniciando programa")
run_simulation = Simulation(routePoints,algorithm)
run_simulation.start()

#Start com lista
#sensor = ["vision"]
#Start(routePoints,sensor)

#Start com dicionario
#Start(routePoints,algorithm)
