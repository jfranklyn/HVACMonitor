
'''
Main code for MQTT client to control the ESP8266 and 
Adafruit INA260 Current+Voltage+Power sensor
relayMQTT topic = hvac-monitor
Using io.adafruit.com dashboard to control the sensors
'''
import time
from umqttsimple import MQTTClient
import machine
import network

ssid = 'ATT-4009'
password = 'Jayden2012'
mqtt_broker = '192.168.1.87'
keep_alive=60
QOS1=1
QOS2=0
CLEAN_SESSION=False
port=1883
last_message = 0
message_interval = 5

# added code to publish sensor connection status
client_id = b'insidevoltcurpow'
connection_status_topic=b'sensors/connected/'+client_id
topic_pub_voltcurr = b'hvac-monitor/inside/voltcurpow'

def on_disconnect(client, userdata, flags, rc=0):
    m="DisConnected flags"+"result code "+str(rc)
    print(m)
    client.publish(connection_status_topic,"False",0,True)
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

station = network.WLAN(network.STA_IF)

station.active(True)
station.connect(ssid, password)

while station.isconnected() == False:
  pass

print('Station connection successful')

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

  client.set_last_will(connection_status_topic,connection_status_topic+' '+"False",0,True) #set will message
  print("connecting ",mqtt_broker)
  client.connect()  
  
  client.publish(connection_status_topic,connection_status_topic+' '+"True",0,True)#use retain flag  
  return client
  
def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  client.publish(connection_status_topic,connection_status_topic+' '+"False",0,True)
  client.disconnect()
  time.sleep(10)
  machine.reset()

def read_sensor():
    time.sleep_ms(6000) # 1 minute
    voltcurrpow = '4.6 3.1 9.9' # voltage current power
    
    return voltcurrpow

try:
  client = connect_mqtt()
except Exception as e:
  restart_and_reconnect()

while True:
  try:
    if (time.time() - last_message) > message_interval:
      voltcurrpow = read_sensor()
      print(topic_pub_voltcurr+' '+voltcurrpow)
      # add the topic and the sensor reading to the published msg
      client.publish(topic_pub_voltcurr, (topic_pub_voltcurr+' '+voltcurrpow))
      last_message = time.time()
  except Exception as e:
    restart_and_reconnect()
    



