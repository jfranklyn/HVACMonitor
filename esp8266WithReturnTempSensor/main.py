
'''
Main code for MQTT client to control the ESP8266 and 
DS18B20 1-wire waterproof temperature sensor using GPIO pin 14
relayMQTT topic = hvac-monitor
Using io.adafruit.com dashboard to control the sensors
'''
import time
from umqttsimple import MQTTClient
import ubinascii
import machine
import micropython
import network
import esp
from machine import Pin
import onewire
import ds18x20
esp.osdebug(None)
import gc
gc.collect()

ssid = 'ATT-4009'
password = 'Jayden2012'
mqtt_broker = '192.168.1.87'
keep_alive=60
QOS1=1
QOS2=0
CLEAN_SESSION=False
port=1883


#client_id = ubinascii.hexlify(machine.unique_id())
# added code to publish sensor connection status
client_id = b'returnairtemperature'
connection_status_topic=b'sensors/connected/'+client_id
topic_pub_temp = b'hvac-monitor/returnair/temperature'

def on_disconnect(client, userdata, flags, rc=0):
    m="DisConnected flags"+"result code "+str(rc)
    print(m)
    client.connected_flag=False

def on_connect(client, userdata, flags, rc):
    if rc==0:
        print("connected OK Returned code=",rc)
        client.connected_flag=True #Flag to indicate success
    else:
        print("Bad connection Returned code=",rc)
        client.bad_connection_flag=True
        
def on_log(client, userdata, level, buf):
    print("log: ",buf)
    
def on_message(client, userdata, message):
    print("message received  "  ,str(message.payload.decode("utf-8")))
    

last_message = 0
message_interval = 5

station = network.WLAN(network.STA_IF)

station.active(True)
station.connect(ssid, password)

while station.isconnected() == False:
  pass

print('Connection successful')

ds_pin = machine.Pin(14)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

def connect_mqtt():
  global client_id, mqtt_server
  client = MQTTClient(client_id, mqtt_broker, port, None, None, 60) # set keepalive = 60
  
  client.connected_flag=False #create flags
  client.bad_connection_flag=False #
  client.retry_count=0 #
  
  client.on_connect=on_connect        #attach function to callback
  client.on_disconnect=on_disconnect  
  
  print("publising on ",connection_status_topic )
  print("Setting will message")

  client.set_last_will(connection_status_topic,"False",0,True) #set will message
  print("connecting ",mqtt_broker)
  client.connect()  
  
  #client = MQTTClient(client_id, mqtt_server, user=your_username, password=your_password)
  #client.connect()
  #print('Connected to %s MQTT broker' % (mqtt_server))
  client.publish(connection_status_topic,"True",0,True)#use retain flag  
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  client.publish(connection_status_topic,"False",0,True)
  client.disconnect()
  time.sleep(10)
  machine.reset()

def read_sensor():
  try:
    roms = ds_sensor.scan()
    ds_sensor.convert_temp()
    time.sleep_ms(60000) # 1 minute
    for rom in roms: 
      temp = ds_sensor.read_temp(rom)
      # uncomment for Fahrenheit
      temp = temp * (9/5) + 32.0
    if (isinstance(temp, float) or (isinstance(temp, int))):
      temp = (b'{0:3.1f}'.format(temp))
      return temp
    else:
      return('Invalid sensor readings.')
  except OSError as e:
    return('Failed to read sensor.')
    
  except Exception as oe:
    print(type(oe), oe)    
    return('Exception Error reading sensor.')
    
try:
  client = connect_mqtt()
except OSError as e:
  restart_and_reconnect()

while True:
  try:
    if (time.time() - last_message) > message_interval:
      temp = read_sensor()
      print(topic_pub_temp+' '+temp)
      # add the topic and the sensor reading to the published msg
      client.publish(topic_pub_temp, (topic_pub_temp+' '+temp))
      last_message = time.time()
  except Exception as e:
    restart_and_reconnect()






