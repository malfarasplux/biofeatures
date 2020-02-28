/*
The following code is based on following examples:

https://github.com/adafruit/Adafruit_MPRLS/blob/master/examples/mprls_simpletest/mprls_simpletest.ino
https://github.com/arduino-libraries/MKRMotorCarrier/blob/master/examples/Motor_test/Motor_test.ino
p_sanches Serverbit code

*/


#include <MKRMotorCarrier.h>
#include <Wire.h>
#include "Adafruit_MPRLS.h"
#include <WiFiNINA.h>
#include <WiFiUdp.h>
#include <OSCMessage.h>
#include <OSCBundle.h>
#include <OSCBoards.h>

#define RESET_PIN  -1  // set to any GPIO pin # to hard-reset on begin()
#define EOC_PIN    -1  // set to any GPIO pin to read end-of-conversion by pin
Adafruit_MPRLS mpr = Adafruit_MPRLS(RESET_PIN, EOC_PIN);

int inflatePower = 0;

char ssid[] = "annie";        // your network SSID (name)
char pass[] = "30894143";    // your network password (use for WPA, or use as key for WEP)
int status = WL_IDLE_STATUS;     // the WiFi radio's status

unsigned int localPort = 12000;      // local port to listen on
char packetBuffer[255]; //buffer to hold incoming packet

WiFiUDP Udp;

// Listening to IPs (Servers: Processing, python) 
const IPAddress serverIp(192, 168, 0, 100); // 192, 168, 0, 140
const unsigned int serverPort = 32000;

const IPAddress pythonIp(192, 168, 0, 100);
const unsigned int pythonPort = 31000;


// My Arduino IP
IPAddress ip(192, 168, 0, 220);    


unsigned long time_now = 0; //in order to keep the time so that we can simulate delay() without blocking the loop() function
int period = 20;  //how often in miliseconds to send the pressure to the server

unsigned long time_now_connect_server = 0; //in order to keep the time so that we can simulate delay() without blocking the loop() function
int period_connect_server = 5000;  //how often in miliseconds to reconnect actuator to server

bool change_actuation = true;

void setup() {
  // put your setup code here, to run once:
Serial.begin(9600);

  //while (!Serial) {
     // wait for serial port to connect. Needed for native USB port only
 // }

// checking the presence of MKR Motor Shield  
  if (controller.begin()) 
    {
      Serial.print("MKR Motor Shield connected, firmware version ");
      Serial.println(controller.getFWVersion());
    } 
  else 
    {
      Serial.println("Couldn't connect! Is the red led blinking? You may need to update the firmware with FWUpdater sketch");
      while (1);
    }
// checking the MPRLS pressure sensor
if (! mpr.begin()) {
    Serial.println("Failed to communicate with MPRLS sensor, check wiring?");
    while (1) {
      delay(10);
    }
  }
  Serial.println("Found MPRLS sensor");

// Establish Arduino IP
  WiFi.config(ip);

// attempt to connect to WiFi network:
  while ( status != WL_CONNECTED) {
    Serial.print("Attempting to connect to WPA SSID: ");
    Serial.println(ssid);
    // Connect to network:
    status = WiFi.begin(ssid);

    // wait 10 seconds for connection:
    delay(10000);
  }

  // you're connected now, so print out the data:
  Serial.print("You're connected to the network");
  printCurrentNet();
  printWiFiData();

  Serial.print("\nStarting listening on port:");
  Serial.print(localPort);
  // if you get a connection, report back via serial:
  Udp.begin(localPort);



  //register with server
  connectToServer();
  delay(50);



}

void loop() {

    char incomingByte = 0;   // for incoming serial data
      if (Serial.available() > 0) {
        // read the incoming byte:
        incomingByte = Serial.read();
        if (incomingByte == 'c') { //if you write 'c' in the command line, it will connect to the server at the specified IP address above
          connectToServer();
          delay(50);
        }
      }

    OSCBundle bundleIN;
    int size;

    if ( (size = Udp.parsePacket()) > 0)
    {
  
      while (size--)
        bundleIN.fill(Udp.read());
  
      if (!bundleIN.hasError())
      {
  
        bundleIN.dispatch("/actuator/inflate", routeInflate);
        bundleIN.dispatch("/actuator/deflate", routeDeflate);
        bundleIN.dispatch("/actuator/inflatedur", routeInflateDur);
        bundleIN.dispatch("/actuator/deflatedur", routeDeflateDur);
        bundleIN.dispatch("/0/raw", routeRiot);
  
      }
    }


    if(change_actuation&&(inflatePower>=-100)&&(inflatePower<=-11))
    {
          deflate();
    
      }

    if (change_actuation&&(inflatePower>-11)&&(inflatePower<11))
    {
          hold();
    
      }

    if (change_actuation&&(inflatePower>=11)&&(inflatePower<=100))
    {
          inflate();
      }

    //we send the pressure in a OSC message to the server every some miliseconds, specified in the variable 'period'
    
    
    if(millis() > time_now + period){
        time_now = millis();
        sendOSCPressure(getPressure());
    }

    //this is just while Pavel does not add physical buttons! WHen he does, delete this code
     if(millis() > time_now_connect_server + period_connect_server){
        time_now_connect_server = millis();
        sendOSCPressure(getPressure());
        connectToServer();
        delay(50);
    }
     
}

void routeRiot(OSCMessage &msg){
  if (msg.isFloat(0)){
      Serial.println(msg.getFloat(0));
  }
  if (msg.isString(0)){
      //Serial.println(msg.getString(0));
  }
}

void routeInflate(OSCMessage &msg) {
  //returns true if the data in the first position is a float
  if (msg.isFloat(0)) {
    //get that float
    float data = msg.getFloat(0);

    if(data >= 0){
      Serial.println("Message received: Inflate");
    }
    if(data < 0){
      Serial.println("Message received: Deflate");
    }

    if(((int) data) != inflatePower){
      change_actuation = true;
    }
    else {
      change_actuation = false;
    }
    
    //Serial.println(data);
    inflatePower = (int) data;
  }
  else {
    Serial.println("Message does not contain a float");
  }
}

void routeDeflate(OSCMessage &msg) {
}

void routeInflateDur(OSCMessage &msg) {
}

void routeDeflateDur(OSCMessage &msg) {
}



void inflate()
{
    M1.setDuty(inflatePower);
    M2.setDuty(0);
    M3.setDuty(0);
    M4.setDuty(40);
   // Serial.println("Inflate");
  
  }

void deflate()
{
    M1.setDuty(abs(inflatePower));
    M2.setDuty(0);
    M3.setDuty(40);
    M4.setDuty(0);
    //Serial.println("Deflate");
  }
  
void hold()
{
    M1.setDuty(0);
    M2.setDuty(0);

    //if we isolate the pillow from the motor loop 
    //M3.setDuty(40);
    //M4.setDuty(40);
    //or we keep the pillow connected to the motor loop - may add air leakage to the system
    M3.setDuty(0);
    M4.setDuty(0);

    
   // Serial.println("Hold");
  }

float getPressure()
{
    float pressure_hPa = mpr.readPressure();
    //Serial.print("Pressure (hPa): "); 
    //Serial.println(pressure_hPa);
    //Serial.print(" ");
    //Serial.print("Pressure (PSI): "); 
    //Serial.println(pressure_hPa / 68.947572932); 

    //stop inflatable when the pressure is getting too high
    if (pressure_hPa > 1200 && inflatePower > 0){
      Serial.println("Pressure too high");
      inflatePower = 0;
      hold();
    }

    //pad is fully deflated
    if (pressure_hPa < 800 && inflatePower < 0){
      Serial.println("Fully deflated");
      inflatePower = 0;
      hold();
    }
    
    return pressure_hPa;
}  

void sendOSCPressure(float pressure) {
  //the message wants an OSC address as first argument
  OSCMessage msg("/sensor/pressure");
  msg.add(pressure);

  OSCMessage msg2("/sensor/pressure");
  msg2.add(pressure);

  Udp.beginPacket(serverIp, serverPort);
  msg.send(Udp); // send the bytes to the SLIP stream
  Udp.endPacket(); // mark the end of the OSC Packet
  msg.empty(); // free space occupied by message

  Udp.beginPacket(pythonIp, pythonPort);
  msg2.send(Udp); // send the bytes to the SLIP stream
  Udp.endPacket(); // mark the end of the OSC Packet
  msg2.empty(); // free space occupied by message

  delay(20);
}

void connectToServer() {

  //Serial.print("\nConnecting to server bit at ");
  //Serial.print(serverIp); Serial.print(":"); Serial.println(serverPort);

  OSCMessage msg("/actuator/startConnection/");

  Udp.beginPacket(serverIp, serverPort);
        
  msg.send(Udp); // send the bytes to the SLIP stream

  Udp.endPacket();

  msg.empty(); // free space occupied by message
}

void printWiFiData() {
  // print your WiFi shield's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);
  Serial.println(ip);

  // print your MAC address:
  byte mac[6];
  WiFi.macAddress(mac);
  Serial.print("MAC address: ");
  //printMacAddress(mac);

}

void printCurrentNet() {
  // print the SSID of the network you're attached to:
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // print the MAC address of the router you're attached to:
  byte bssid[6];
  WiFi.BSSID(bssid);
  Serial.print("BSSID: ");
  printMacAddress(bssid);

  // print the received signal strength:
  long rssi = WiFi.RSSI();
  Serial.print("signal strength (RSSI):");
  Serial.println(rssi);

  // print the encryption type:
  byte encryption = WiFi.encryptionType();
  Serial.print("Encryption Type:");
  Serial.println(encryption, HEX);
  Serial.println();
}

void printMacAddress(byte mac[]) {
  for (int i = 5; i >= 0; i--) {
    if (mac[i] < 16) {
      Serial.print("0");
    }
    Serial.print(mac[i], HEX);
    if (i > 0) {
      Serial.print(":");
    }
  }
  Serial.println();
}
  
