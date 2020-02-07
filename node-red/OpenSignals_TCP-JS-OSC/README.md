# OpenSignals_TCP-JS-OSC

Example using OpenSignals TCP config to forward BITalino JSON data to a python jupyter notebook that Node-RED picks up as OSC to output MIDI.

* OpenSignals_TCP-JS-OSC [notebook](https://github.com/malfarasplux/biofeatures/blob/master/notebooks/mServer.ipynb)  
* OpenSignals_TCP-JS-OSC [flow](https://github.com/malfarasplux/biofeatures/blob/master/node-red/OpenSignals_TCP-JS-OSC/OpenSignals_TCP-JS-OSC.json)  

![Flowimg](/img/flows/flow_OpenSignals_TCP-JS-OSC.jpg)


### Prerequisites  
* [Node-RED](https://nodered.org/)  
* Node-RED [MIDI](https://flows.nodered.org/node/node-red-contrib-midi) and [OSC](https://flows.nodered.org/node/node-red-contrib-osc) contrib  
* [OpenSignals](https://bitalino.com/en/software)
* [Jupyter](https://jupyter.org/)

#### Additional (MIDI virtual port and interface)  
* [Dexed](https://asb2m10.github.io/dexed/)  
* [LoopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html)  
