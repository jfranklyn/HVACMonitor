#######################################################################
# hvacMQTT.py - Monitors a Mosquitto MQTT queue for hvac events
# from an array of sensors, detects critical changes in those
# sensor values, and injects alarms into an io.adafruit.com queue.
# DS8266 HUZZAH WiFi
# sensors include DS18B20 - 1-wire temperature sensor
# INA260 - DC/Current/Power monitor
# MLX90614 3V - infrared temperature sensor
# All sensors purchased from Adafruit
#######################################################################

########################
# Libraries
########################

import os
import string
import paho.mqtt.client as mqtt
import Adafruit_IO
from Adafruit_IO import Client, RequestError
import time


########################
# Globals
########################

# -- Change these as needed for your installatin --

localBroker = "192.168.1.87"        # Local MQTT broker
localPort = 1883            # Local MQTT port
localUser = "jfranklyn"         # Local MQTT user
localPass = "Jaf_10205!"            # Local MQTT password
localTopic = "hvac-monitor"        # Local MQTT topic to monitor
localTimeOut = 120          # Local MQTT session timeout

adafruitUser = "jfranklyn"      # Adafruit.IO user ID
adafruitKey = "aio_CHEe10hCx2u0UyllHFi1UltiIu8V"    # Adafruit.IO user key
adafruitTopic = "hvac-monitor"        # Adafruit.IO alarm topic
LOOP_INTERVAL = 15 # seconds

sensorList = {}             # List of sensor objects

########################
# Classes and Methods
########################

class sensor():
    def __init__(self):
        self.name = ""      # Name of sensor in MQTT
        self.humanName = "" # Human-meaningful name (e.g., "front door")
        self.lastSeen = 0   # Number of seconds since the sensor was last seen
        self.state = "unknown"  # State of the object: unknown, open, or closed

    def setState(self, newstate):
        self.state = newState

    def getState(self):
        return self.state

    def resetHeartbeat(self):
        self.lastSeen = 0

    def setname(self, newName, humanName):
        self.name = newName
        self.humanName = humanName

    def getname(self):
        return self.humanName

    def checkState(self, newState):
        if ("unknown" == self.state):
            self.state = newState
            return 0
        else:
            if (newState != self.state):
                self.state = newState
                if ("closed" == self.state):
                    return -1
                else:
                    return 1
        return 0
        

class sensorList():
    def __init__(self):
        self.sensorList = {}

    def addSensor(self, sensorName, humanName):
        self.sensorList[sensorName] = sensor()
        self.sensorList[sensorName].setname(sensorName, humanName)

    def getSensorName(self, sensorID):
        return self.sensorList[sensorID].getname()

    def sensorState(self, sensorID, monitorState):
        rv = self.sensorList[sensorID].checkState(monitorState)
        if (0 != rv):
            # State changed!
            if (0 > rv):
                outBuf = "INFO "+self.getSensorName(sensorID)+" "+monitorState
                print(outBuf)
            else:
                outBuf = "ALARM "+self.getSensorName(sensorID)+" "+monitorState
                print(outBuf)
                print("Initiating connection to Adafruit.IO")
                AIOclient = Adafruit_IO.MQTTClient(adafruitUser, adafruitKey)
                print("Setting callbacks for Adafruit.IO")
                AIOclient.on_connect = AIOconnected
                AIOclient.on_disconnect = AIOdisconnected
                AIOclient.on_message = AIOmessage
                print("Connecting to Adafruit.IO")
                AIOclient.connect()
                time.sleep(5)
                print("Publishing outBuf")
                # AIOclient.publish("alarms", outBuf)
                AIOclient.publish("hvac-monitor", outBuf)
                print("Disconnecting")
                AIOclient.disconnect()


########################
# Functions
########################

# Callback functions for Adafruit.IO connections
def AIOconnected(client):
    # client.subscribe('hvac-monitor')
    print("Connected to Adafruit.IO")

def AIOdisconnected(client):
    print("adafruit.io client disconnected!")

def AIOmessage(client, feed_id, payload):
    print("adafruit.io received ", payload)


# returnState takes a numeric voltage value from the sensor and
# returns the state of the monitored device. With a voltage divider
# that uses a 1M ohm R1 and a 470K ohm R2, the "closed" state returns
# 1024 and the open state returns between 1 and 40.

def returnState(inVal):
    if (1000 < inVal):
        return "closed"
    if (100 > inVal):
        return "open"
    else:
        return "unknown"

# Create an instance of the REST client
aio = Client(adafruitUser, adafruitKey)
# Setup AdaFruit IO feeds
alarm_feed = aio.feeds('hvac-monitor')
return_air_feed = aio.feeds('return-air')
supply_air_feed = aio.feeds('supply-air')
suction_line_feed = aio.feeds('suction-line')
supply_line_feed = aio.feeds('supply-line')
volt_ctrl_indoor_feed = aio.feeds('volt-crtl-indoor')
current_ctrl_indoor_feed = aio.feeds('curr-crtl-indoor')

########################
# Main
########################

def main():

    while True:
        sensList = sensorList()
        sensList.addSensor("return_air_temp", "return air temperature")
        sensList.addSensor("supply_air_temp", "supply air temperature")
        sensList.addSensor("suction_line_temp", "suction line temperature")
        sensList.addSensor("supply_line_temp", "supply line temperature")
        sensList.addSensor("volt_ctrl_indoor", "volt ctrl indoor")
        sensList.addSensor("volt_ctrl_outdoor", "volt ctrl outdoor")
        sensList.addSensor("curr_ctrl_indoor", "current ctrl indoor")
        sensList.addSensor("curr_ctrl_outdoor", "current ctrl outdoor")
        
        # The callback for when the client receives a CONNACK response from the server.
        def on_connect(client, userdata, flags, rc):
            print("Connected with result code "+str(rc))

            # Subscribing in on_connect() means that if we lose the connection and
            # reconnect then subscriptions will be renewed.
            client.subscribe("hvac-monitor")

        # The callback for when a PUBLISH message is received from the server.
        def on_message(client, userdata, msg):
            print('payload= ',msg.payload)
            # convert byte literals (python2) to strings
            payloadstr = msg.payload.decode('UTF-8')
            (sensorID, sensorVoltage) = payloadstr.split()
            #print('id voltage ', sensorID, sensorVoltage)
            sensorVoltage = int(sensorVoltage)
            sensorName = sensList.getSensorName(sensorID)
            sensList.sensorState(sensorID, returnState(sensorVoltage))
            # print(sensorName+" "+returnState(sensorVoltage))

        client = mqtt.Client()
        client.connect(localBroker, localPort, localTimeOut)
        client.on_connect = on_connect
        client.on_message = on_message
        
        # check the state of the AIO lights toggle
        indoor_light_status = aio.receive(indoor_lights_feed.key)
        if indoor_light_status.value == 'OFF':
            #print ('AIO light switch toggle = OFF')
            client.publish(localTopic, "RPI Zero W Online")
            
            # Blocking call that processes network traffic, dispatches callbacks and
            # handles reconnecting.
            # Other loop*() functions are available that give a threaded interface and a
            # manual interface.
        time.sleep(LOOP_INTERVAL)
        #client.loop_forever()
##        print ('We are quitting')
##        quit()

if __name__ == "__main__":
    main()    
