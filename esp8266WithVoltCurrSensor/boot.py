'''
This file is executed on every boot (including wake-boot from deepsleep)
Make a connection to the WLAN
'''
import time
#from umqttsimple import MQTTClient
#import ubinascii
#import machine
import micropython
import network
import esp
esp.osdebug(None)
import gc
gc.collect()

ssid = 'ATT-4009'
password = 'Jayden2012'
mqtt_server = '192.168.1.87'
#EXAMPLE IP ADDRESS
#mqtt_server = '192.168.1.144'
#client_id = ubinascii.hexlify(machine.unique_id())
# added code to publish sensor connection status
client_id = b'insidevoltcurr'
connection_status_topic=b'sensors/connected/'+client_id
topic_pub_voltcurr = b'hvac-monitor/inside/voltcurr'
try:
  station = network.WLAN(network.STA_IF)
  station.active(True)
  station.connect(ssid, password)
  
  if station.isconnected() == True:
    print('Connection successful '+client_id)
    print(station.ifconfig())
  
except Exception as e:
  print('Connection Exception '+e)    

