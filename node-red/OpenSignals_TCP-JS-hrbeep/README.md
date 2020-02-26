# OpenSignals_TCP-JS-hrbeep

Example using OpenSignals TCP config to forward BITalino ECG JSON data to Node-RED, sending thresholded heart rate beeps to MIDI output.  
ECG is set up as RAW A1.  
Threshold is based on RAW data resolution for BITalino (10 bit --> 1024).  


* OpenSignals_TCP-JS-hrbeep [flow](https://github.com/malfarasplux/biofeatures/blob/master/node-red/OpenSignals_TCP-JS-hrbeep/OpenSignals_TCP-JS-hrbeep.json)  

![Flowimg](/img/flows/flow_hrbeep.jpg)


### Prerequisites  
* [Node-RED](https://nodered.org/)  
* Node-RED [MIDI](https://flows.nodered.org/node/node-red-contrib-midi) 
* [OpenSignals](https://bitalino.com/en/software)
 
 Set up a device and a TCP port on the acquisition software
 <img src="/img/TCP_setup.jpg" width="600"  />


#### Additional (MIDI virtual port and interface)  
* [Dexed](https://asb2m10.github.io/dexed/)  
* [LoopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html)  


#### Alternative
* [OSC](https://flows.nodered.org/node/node-red-contrib-osc)    
* [Music](https://flows.nodered.org/node/node-red-contrib-music)  
* [SuperCollider](https://supercollider.github.io/)
A beep can also be created by sending a music kick OSC command to SuperCollider  
