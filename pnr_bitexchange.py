from pynodered import node_red
import numpy as np
import time
from bitalino import BITalino

isAcquiring = 0
data = []
data = np.arange(100)
npending = 0 
stime = int(time.time())

@node_red(category="pyfuncs")
def BITalinoNode(node, msg):
    global isAcquiring, data, npending, stime

    if msg['payload']['pyJSON'] == True:
            if msg['payload']['type']=="BITalino":
                if msg['payload']['macAddress']!="":
                    launch_acquisition(msg)
            elif msg['payload']['type']=="stop":
                isAcquiring = 0
            elif msg['payload']['type']=="print":
                npending = int(time.time()) - stime
                msg['payload']['val']=data[-npending:].tolist()
                stime = int(time.time())

    return msg

   
def set_acquisition():

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

def launch_acquisition(msg):
    global isAcquiring, data, npending, stime
    isAcquiring = 1
    macAddress = msg['payload']['macAddress']

    # This example will collect data for 5 sec.
    running_time = 9
        
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

    # ON/OFF
    device.trigger([1,1])
    device.trigger([0,0])

    # Start Acquisition
    device.start(samplingRate, acqChannels)

    start = time.time()
    end = time.time()
    while (end - start) < running_time and isAcquiring == 1 :
        # Read samples
        data = device.read(nSamples)
        print(data)
        msg['payload']['val']=data.tolist()
        end = time.time()
        
    # Stop acquisition
    device.stop()
        
    # Close connection
    device.close()
    isAcquiring = 0
    return ("success")