
'''
Main code for MQTT client to control the ESP8266 and 
BME280 temperature, humidity, baro pressure sensor
relayMQTT topic = hvac-monitor
Using io.adafruit.com dashboard to control the sensors
'''
from umqttsimple import MQTTClient
import micropython
import network
import machine
from machine import Pin, I2C
from time import time, sleep
import BME280

keep_alive=60
QOS1=1
QOS2=0
CLEAN_SESSION=False
port=1883

try:
    from secrets import secrets
except ImportError as imp_err:
    print("WiFi secrets are kept in secrets.py, error {}".format(imp_err))
    raise
    
# added code to publish sensor connection status
client_id = b'interiortemppreshum'
connection_status_topic=b'sensors/connected/'+client_id
topic_pub_temp = b'hvac-monitor/interior/temppreshum'

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

# Check WiFi connection and re-connect if needed
station = network.WLAN(network.STA_IF)

while station.isconnected() == False:
  station.active(True)
  station.connect(secrets["ssid"], secrets["password"])
  print('Connection successful')

def connect_mqtt():
  global client_id, mqtt_server
  client = MQTTClient(client_id, secrets["mqtt_broker"], port, None, None, 60) # set keepalive = 60
  
  client.connected_flag=False #create flags
  client.bad_connection_flag=False #
  client.retry_count=0 #
  
  client.on_connect=on_connect        #attach function to callback
  client.on_disconnect=on_disconnect  
  
  print("publising on ",connection_status_topic )
  print("Setting will message")

  client.set_last_will(connection_status_topic,"False",0,True) #set will message
  print("connecting ",secrets["mqtt_broker"])
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
  # tuple to hold results from sensor
  temppresshumd = ()
  try:
# the BME280 is connected using i2c
    # ESP32 - Pin assignment
    #i2c = I2C(scl=Pin(22), sda=Pin(21), freq=10000)
# ESP8266 - Pin assignment
    i2c = I2C(scl=Pin(5), sda=Pin(4), freq=10000)
# temperature results in celsius
    bme = BME280.BME280(i2c=i2c)
    #temp = bme.temperature
    hum = bme.humidity
    pres = bme.pressure
    
  # uncomment for temperature in Fahrenheit
    temp = (bme.read_temperature()/100) * (9/5) + 32
    temp = str(round(temp, 2)) + 'F'
    
    temppresshumd[0] = temp
    temppresshumd[1] = hum
    temppresshumd[2] = pres

    print(temppresshumd)
    
  except Exception as oe:
    print('BME280 Exception {}'.format(oe))   
   
  return temppresshumd 
        
try:
  client = connect_mqtt()
except OSError as e:
  restart_and_reconnect()

while True:
  try:
    if (time.time() - last_message) > message_interval:
      temppresshumd_vals = read_sensor()
      print(topic_pub_temp+' '+temppresshumd_vals)
      # add the topic and the sensor reading to the published msg
      client.publish(topic_pub_temp, (topic_pub_temp+' '+temppresshumd_vals))
      last_message = time.time()
  except Exception as e:
    restart_and_reconnect()










