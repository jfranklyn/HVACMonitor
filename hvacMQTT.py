#!/usr/bin/env python3
"""
 hvacMQTT.py - Monitors a Mosquitto MQTT queue for hvac events
 from an array of sensors, detects critical changes in those
 sensor values, and injects alarms into an io.adafruit.com queue.
 ESP32-S2 Feather S2 WiFi - unexpectedmaker.com
 sensors include DS18B20 - 1-wire temperature sensor
 INA260 - DC/Current/Power monitor
 MLX90614 3V - infrared temperature sensor
 All sensors purchased from Adafruit
 Added logging. Errors to a file. info messages to the console
 Added 16x2 LCD screen for output msg. Sensor readings can go to the LCD or AIO

"""

########################
# Libraries
########################

import os
import string
import paho.mqtt.client as mqtt
import Adafruit_IO
from Adafruit_IO import Client, RequestError
import time
import coloredlogs, logging, sys
from datetime import datetime
import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd

########################
# Globals
########################
# configuration for 16x2 RGB display
lcd_columns = 16
lcd_rows = 2
try:
    
    i2c = busio.I2C(board.SCL, board.SDA)
    lcd = character_lcd.Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)
except Exception as lcd_err:
    logger.error("Cannot connect to i2c LCD display: {} ".format(lcd_err))

# Creating logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
coloredlogs.install(level=logging.DEBUG, logger=logger)

# Handler - file
file = logging.FileHandler("hvacMQTT.log")
fileformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
# log everything that is a warning and above
file.setLevel(logging.WARNING)
file.setFormatter(fileformat)

# Handler - console
stream = logging.StreamHandler()
streamformat = logging.Formatter("%(levelname)s:%(module)s:%(message)s")
# log everything that is a info and above
stream.setLevel(logging.INFO)
stream.setFormatter(streamformat)

# Adding all handlers to the logs
logger.addHandler(file)
logger.addHandler(stream)

try:
    from secrets import secrets
except ImportError:
    logger.error("WiFi secrets are kept in secrets.py, please add them there!")
    raise

localPort = 1883            # Local MQTT port
localTopic = "hvac-monitor"        # Local MQTT topic to monitor
localTimeOut = 120          # Local MQTT session timeout
adafruitTopic = "hvac-monitor"        # Adafruit.IO alarm topic
LOOP_INTERVAL = 5 # seconds

# Create an instance of the REST client for io.adafruit.com dashboard
try:
    global aio
    aio = Client(secrets["aio_username"], secrets["aio_key"])
except Exception as aio_err:
    logger.error("Cannot connect to io.adafruit.com with error: {} ".format(aio_err))
    raise    
#aio = Client(adafruitUser, adafruitKey)
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
indoor_vcp_status = aio.feeds('indoor-vcp-status')
outdoor_vcp_status = aio.feeds('outdoor-vcp-status')

########################
# Functions
########################
'''
send the sensor message text to the screen/aio or both
    sensor = mqtt sensor name
    msg = text from sensor
    screen_row = lcd screen row. 2 rows max
    screen_out = output text to lcd screen
    aio_out = output text to io.adafruit.com
'''
def display_sensor_reading(sensor, msg='none', screen_row=1,screen_out=1, aio_out=0):

    # set LCD color to blue
    lcd.color = [100, 0, 0]
    lcd.row = screen_row
    
    # check for aio rest client connection
    if (aio.base_url == ''):
        logger.error("No connection to AIO website found")
        aio_out=0
        return
    
    if (screen_out):
        # Create message to scroll
        scroll_msg =  sensor + ' : ' + str(msg)
        lcd.message = scroll_msg
        # Scroll to the left
        for i in range(len(scroll_msg)):
            time.sleep(0.5)
            lcd.move_left()
        lcd.clear()

    if (aio_out):
        aio.send(sensor,msg)
    
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    logger.info("Connected with sensor client result code {}".format(str(rc)))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # add subscription here as needed for each sensor
    client.subscribe("hvac-monitor")
    client.subscribe("hvac-monitor/returnair/temperature")
    client.subscribe("hvac-monitor/supplyair/temperature")
    client.subscribe("hvac-monitor/suctionline/temperature")
    client.subscribe("hvac-monitor/liquidline/temperature")
    client.subscribe("hvac-monitor/inside/voltage")
    client.subscribe("hvac-monitor/inside/current")
    client.subscribe("hvac-monitor/inside/power")
    client.subscribe("hvac-monitor/outside/voltage")
    client.subscribe("hvac-monitor/outside/current")    
    client.subscribe("hvac-monitor/outside/power")
    client.subscribe("hvac-monitor-interior/interior/temppreshum")

# Subscript to sensor connected status messages
    client.subscribe("last-will/connected/insidevoltcurr")
    client.subscribe("last-will/connected/outsidevoltcurr")
    client.subscribe("last-will/connected/returnairtemp")    
    client.subscribe("last-will/connected/supplyairtemp")
    client.subscribe("last-will/connected/suctionlinetemp")
    client.subscribe("last-will/connected/liquidlinetemp")
    
# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    logger.info('Last Will message topic = {} payload= {}'.format(msg.topic, msg.payload))
    # convert byte literals (python2) to strings
    payloadstr = msg.payload.decode('UTF-8')
    msgtopicstr = msg.topic

# check the connection status of the sensors
    sensorconn_str = "last-will/connected"
    if(sensorconn_str in msgtopicstr):
        # check for sensor failures
        # handle sensor status messages
        if((msgtopicstr=="last-will/connected/insidevoltcurr") and (payloadstr != '1')):
            # turn the sensor red to show that it is offline
            aio.send('indoor_vcp_status','OFF')
            logger.error('ina260 sensor offline {}'.format(payloadstr))
            return
        else:
            aio.send('indoor-vcp-status','ON')
        
        if (payloadstr == 'ina260 circuit overloaded'):
            aio.send('indoor_vcp_status','OFF')
            logger.info('ina260 sensor overloaded {}'.format(payloadstr))
            return
        else:
            aio.send('indoor-vcp-status','ON')

# turn aio gauges to their warning value if the sensor is offline
        if ((msgtopicstr == 'last-will/connected/insidevoltcurr') and (payloadstr != '1')):
            aio.send('indoor_vcp_status','OFF')
            logger.info('Sensor {} is offline '.format(msgtopicstr))
        if ((msgtopicstr == 'last-will/connected/outsidevoltcurr') and (payloadstr != '1')):
            logger.info('Sensor {} is offline '.format(msgtopicstr))
            aio.send('outdoor_vcp_status','OFF')
        if ((msgtopicstr == 'last-will/connected/returnairtemp') and (payloadstr != '1')):
            logger.info('Sensor {} is offline '.format(msgtopicstr))
            aio.send_data('return-air',999)
        if ((msgtopicstr == 'last-will/connected/supplyairtemp') and (payloadstr != '1')):
            aio.send_data('supply-air',999)
            logger.info('Sensor {} is offline '.format(msgtopicstr))            
        if ((msgtopicstr == 'last-will/connected/suctionlinetemp') and (payloadstr != '1')):
            aio.send_data('suction-line',999)
            logger.info('Sensor {} is offline '.format(msgtopicstr))
        if ((msgtopicstr == 'last-will/connected/liquidlinetemp') and (payloadstr != '1')):
            aio.send_data('supply-line',999)
            logger.info('Sensor {} is offline '.format(msgtopicstr))                       

    sensor_str = "hvac-monitor"
    if(sensor_str == msgtopicstr):
# these messages contain value pairs so process them    
        logger.info('Normal Msg Payload String = {}'.format(payloadstr))

        logger.info('payloadstr = {}'.format(payloadstr))
        logger.info('sensor ID = {}'.format(msgtopicstr))

        try:
            (topic, payload) = payloadstr.split()
        except ValueError as val_err:
            logger.error("Cannot split payload string reason: {} ".format(val_err))
            raise
        
        fsensorValue = float(payload)
        logger.info('float sensorValue = {}'.format(fsensorValue))
        
    # inside sensor reading. display on LCD row = 2
##        if(msgtopicstr=="hvac-monitor-interior/interior/temppreshum"):
##            logger.info('interior temperature pressure humidity = {}'.format(payloadstr))
##            display_sensor_reading('interior temperature pressure humidity =',payloadstr, 2, 1, 0)
    
    # temperature sensors
        if(msgtopicstr=="hvac-monitor/returnair/temperature"):
            logger.info('Return air temp = {}'.format(fsensorValue))
            display_sensor_reading('return-air',fsensorValue, 1, 1, 0)
            #aio.send_data('return-air',fsensorValue)
        if(msgtopicstr=="hvac-monitor/supplyair/temperature"):
            display_sensor_reading('supply-air',fsensorValue, 1, 1, 0)
            #aio.send_data('supply-air',fsensorValue)
        if(msgtopicstr=="hvac-monitor/suctionline/temperature"):
            display_sensor_reading('suction-line',fsensorValue, 1, 1, 0)
            #aio.send_data('suction-line',fsensorValue)
        if(msgtopicstr=="hvac-monitor/liquidline/temperature"):
            display_sensor_reading('supply-line',fsensorValue, 1, 1, 0)
            #aio.send('supply-line',fsensorValue)

    # indoor voltage, current, power sensors           
        if(msgtopicstr=="hvac-monitor/inside/voltage"):
            logger.info('Inside voltage  = {}'.format(fsensorValue))
            display_sensor_reading('volt-ctrl-indoor',fsensorValue, 1, 1, 0)
            #aio.send('volt-ctrl-indoor',fsensorValue)
        if(msgtopicstr=="hvac-monitor/inside/current"):
            logger.info('Inside current  = {}'.format(fsensorValue))
            display_sensor_reading('curr-ctrl-indoor',fsensorValue, 1, 1, 0)
            #aio.send('curr-ctrl-indoor',fsensorValue)
        if(msgtopicstr=="hvac-monitor/inside/power"):
            logger.info('Inside power  = {}'.format(fsensorValue))
            display_sensor_reading('pow-ctrl-indoor',fsensorValue, 1, 1, 0)
            #aio.send('pow-ctrl-indoor',fsensorValue)
            
    # outdoor voltage, current, power sensors          
        if(msgtopicstr=="hvac-monitor/outside/voltage"):
            logger.info('outside Voltage  = {}'.format(fsensorValue))
            display_sensor_reading('volt-ctrl-outdoor',fsensorValue, 1, 1, 0)
            #aio.send('volt-ctrl-outdoor',fsensorValue)
        if(msgtopicstr=="hvac-monitor/outside/current"):
            logger.info('outside current  = {}'.format(fsensorValue))
            display_sensor_reading('curr-ctrl-outdoor',fsensorValue, 1, 1, 0)
            #aio.send('curr-ctrl-outdoor',fsensorValue)
        if(msgtopicstr=="hvac-monitor/outside/power"):
            logger.info('outside power  = {}'.format(fsensorValue))
            display_sensor_reading('pow-ctrl-outdoor',fsensorValue, 1, 1, 0)
            #aio.send('pow-ctrl-outdoor',fsensorValue)

    # interior temperature, humidity, pressure sensors
    # display these values on LCD 2nd row
    if(msgtopicstr=="hvac-monitor/interior/temppreshum"):
        if (len(payloadstr) == 3):
            logger.info('interior Temperature = {}'.format(temppreshum[0]))
            display_sensor_reading('interior-temperature',temppreshum[0], 2, 1, 0)
            logger.info('outside Voltage  = {}'.format(temppreshum[1]))
            display_sensor_reading('interior-humdity',temppreshum[1], 2, 1, 0)
            logger.info('outside Voltage  = {}'.format(temppreshum[2]))
            display_sensor_reading('interior--barometric-pressure',temppreshum[2], 2, 1, 0)
        else:
            logger.error("Invalid BME280 temperature, humidity, pressure sensor reading: {} ".format(payloadstr))

########################    
# Main
########################

def main():

    while 1:
        logger.info(' In main() ') 
        try:
            client = mqtt.Client()
            client.connect(secrets["localBroker"], localPort, localTimeOut)
            logger.info ('connected to MQTT Server')
            lcd.massage = 'connected to MQTT Server'
            client.on_connect = on_connect
            client.on_message = on_message
            
        except Exception as e:
            logger.error('Could not connect to MQTT Server {}{}'.format(type(e).__name__, e))
            
        # check the status of each sensor andreturn the value to the aio dashboard
        client.publish(localTopic, "RPI 4b Broker Online")
        
        time.sleep(LOOP_INTERVAL)
        client.loop_forever()


if __name__ == "__main__":
    main()    

