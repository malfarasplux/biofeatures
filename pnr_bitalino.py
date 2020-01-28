from pynodered import node_red
import numpy as np
import time
from bitalino import BITalino

isAcquiring = 0

@node_red(category="pyfuncs")
def BITalinoNode(node, msg):
    global isAcquiring

    if msg['payload']['pyJSON'] == True:
            if msg['payload']['type']=="BITalino":
                launch_acquisition()
                msg = "START"
            elif msg['payload']['type']=="stop":
                isAcquiring = 0
            elif msg['payload']['type']=="print":
                msg['payload'] = isAcquiring
                  
    return msg

   
def set_acquisition():
    macAddress = ""

    # This example will collect data for 5 sec.
    running_time = 5
        
    batteryThreshold = 30
    acqChannels = [0, 1, 2, 3, 4, 5]
    samplingRate = 1000
    nSamples = 10
    digitalOutput = [1,1]
    
    # Connect to BITalino
    device = BITalino(macAddress)

    # Set battery threshold
    device.battery(batteryThreshold)

def acquire():
    device.read(nSamples)

def launch_acquisition():
    global isAcquiring 
    isAcquiring = 1
    macAddress = ""

    # This example will collect data for 5 sec.
    running_time = 15
        
    batteryThreshold = 30
    acqChannels = [0, 1, 2, 3, 4, 5]
    samplingRate = 1000
    nSamples = 10
    digitalOutput = [1,1]
    
    # Connect to BITalino
    device = BITalino(macAddress)

    # Set battery threshold
    device.battery(batteryThreshold)

    # Read BITalino version
    print(device.version())

    # Start Acquisition
    device.start(samplingRate, acqChannels)

    start = time.time()
    end = time.time()
    while (end - start) < running_time and isAcquiring == 1 :
        # Read samples
        print(device.read(nSamples))
        end = time.time()

    # Turn BITalino led on
    device.trigger(digitalOutput)
        
    # Stop acquisition
    device.stop()
        
    # Close connection
    device.close()
    isAcquiring = 0
    return ("success")