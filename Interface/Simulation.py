from Control.Control import *
from Avoid.Avoid import *
from Detect.Detect import *
from Interface.Communication import AirSimCommunication

class Simulation(Thread):
    avoidThread = None
    detect = None

    def __init__(self,routePoints,sensorsAlgorithms={'Vision':[VisionRDSVMTracker]},avoidClass=Avoid,comunication=AirSimCommunication,showVideo=True):
        Thread.__init__(self)
        self.status = 'start'
        # vehicleComunication = comunication.getVehicle()
        # Conectando ao simulador AirSim
        print("Communication")
        self.vehicleComunication = AirSimCommunication()
        self.control = Control(self.vehicleComunication,routePoints)

        if avoidClass is not None:
            self.avoidThread  = avoidClass(self.control)
        if sensorsAlgorithms is not None:
            self.detect = Detect(self.vehicleComunication,sensorsAlgorithms,self.avoidThread)
        #self.start()

    def run(self):
        self.control.start()
        #Start thread detect and avoid
        if self.detect is not None:
            self.detect.start()
        #if self.avoidThread is not None:
        #    self.avoidThread.start()
        #Run threads detect and avoid
        if self.detect is not None:
            self.detect.join()
        #if self.avoidThread is not None:
        #    self.avoidThread.join()

    def end_run(self):
        pass

    def get_status(self):
        return self.status
