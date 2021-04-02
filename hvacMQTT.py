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
adafruitKey = "aio_FwbW409G1wKMn6ulWV9B1j56FKX6"    # Adafruit.IO user key
adafruitTopic = "hvac-monitor"        # Adafruit.IO alarm topic
LOOP_INTERVAL = 5 # seconds

########################
# Functions
########################

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with sensor client result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # add subscription here as needed for each sensor
    client.subscribe("hvac-monitor")
    client.subscribe("hvac-monitor/returnair/temperature")
    client.subscribe("hvac-monitor/supplyair/temperature")
    client.subscribe("hvac-monitor/suctionline/temperature")
    client.subscribe("hvac-monitor/liquidline/temperature")
    client.subscribe("hvac-monitor/inside/voltcurpow")
    client.subscribe("hvac-monitor/inside/current")
    client.subscribe("hvac-monitor/inside/power")
    client.subscribe("hvac-monitor/outside/voltcurpow")
    client.subscribe("hvac-monitor/outside/current")    
    client.subscribe("hvac-monitor/outside/power")

# Subscript to sensor connected status messages
    client.subscribe("sensors/connected/insidevoltcurr")
    client.subscribe("sensors/connected/outsidevoltcurr")
    client.subscribe("sensors/connected/returnairtemp")    
    client.subscribe("sensors/connected/supplyairtemp")
    client.subscribe("sensors/connected/suctionlinetemp")
    client.subscribe("sensors/connected/liquidlinetemp")
    
# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print('payload= ',msg.payload)
    # convert byte literals (python2) to strings
    payloadstr = msg.payload.decode('UTF-8')

    try:
        (sensorID, sensorValue) = payloadstr.split()

    except ValueError as ve:
        print('Value error reading sensor {}{}{}'.format(type(ve).__name__, ve, payloadstr))
  
    fsensorValue = float(sensorValue)
    print('sensor ID = ', sensorID)
    print('float sensorValue = ', fsensorValue)
    print('sensorValue = ', sensorValue)
    
# temperature sensors
    if(sensorID=="hvac-monitor/returnair/temperature"):
        print('Return air temp = ', fsensorValue)
        aio.send_data('return-air',fsensorValue)
    if(sensorID=="hvac-monitor/supplyair/temperature"):
        aio.send_data('supply-air',fsensorValue)
    if(sensorID=="hvac-monitor/suctionline/temperature"):
        aio.send_data('suction-line',fsensorValue)
    if(sensorID=="hvac-monitor/liquidline/temperature"):
        aio.send('supply-line',fsensorValue)

# indoor voltage, current, power sensors           
    if(sensorID=="hvac-monitor/inside/voltcurpow"):
        print('Inside Voltage Current Power = ', fsensorValue)
        (fvolts, fcurrent, fpower) = sensorValue.split()
        aio.send('volt-ctrl-indoor',fvolts)
        aio.send('cur-ctrl-indoor',fcurrent)
        aio.send('pow-ctrl-indoor',fpower)
        
# outdoor voltage, current, power sensors          
    if(sensorID=="hvac-monitor/outside/volcurpow"):
        aio.send('volt-ctrl-outdoor',fsensorValue)
    if(sensorID=="hvac-monitor/outside/current"):
        aio.send('curr-ctrl-outdoor',fsensorValue)
    if(sensorID=="hvac-monitor/outside/power"):
        aio.send('pow-ctrl-outdoor',fsensorValue)

# handle sensor status messages
    if((sensorID=="sensors/connected/insidevoltcurr") and (sensorValue=='False')):
        # turn the sensor red to show that it is offline
        aio.send('volt-ctrl-indoor',999)

# Create an instance of the REST client
aio = Client(adafruitUser, adafruitKey)
# Setup AdaFruit IO feeds
#alarm_feed = aio.feeds('hvac-monitor')
return_air_feed = aio.feeds('return-air')
supply_air_feed = aio.feeds('supply-air')
suction_line_feed = aio.feeds('suction-line')
supply_line_feed = aio.feeds('supply-line')
volt_ctrl_indoor_feed = aio.feeds('volt-ctrl-indoor')
current_ctrl_indoor_feed = aio.feeds('curr-ctrl-indoor')
power_ctrl_indoor_feed = aio.feeds('pow-ctrl-indoor')
volt_ctrl_outdoor_feed = aio.feeds('volt-ctrl-outdoor')
current_ctrl_outdoor_feed = aio.feeds('curr-ctrl-outdoor')
power_ctrl_outdoor_feed = aio.feeds('pow-ctrl-outdoor')

########################
# Main
########################

def main():

    while True:
 
        try:
            client = mqtt.Client()
            client.connect(localBroker, localPort, localTimeOut)
            print ('connected to MQTT Server')
            client.on_connect = on_connect
            client.on_message = on_message
            
        except Exception as e:
            print('Could not connect to MQTT Server {}{}'.format(type(e).__name__, e))
            
        # check the status of each sensor andreturn the value to the aio dashboard
        client.publish(localTopic, "RPI Zero W Online")
        
        time.sleep(LOOP_INTERVAL)
        client.loop_forever()

##        print ('We are quitting')
##        quit()

if __name__ == "__main__":
    main()    
