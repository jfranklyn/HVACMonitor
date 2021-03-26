'''
Main code for MQTT client to control the ESP8266 and 
Adafruit INA260 Current+Voltage+Power sensor
relayMQTT topic = hvac-monitor
Using io.adafruit.com dashboard to control the sensors
'''

def sub_cb(topic, msg):
  print((topic, msg))
  if topic == b'hvac-monitor' and msg == b'received':
    print('ESP8266 Curr+Volt+Power Sensor received hello message')

def connect_and_subscribe():
  global client_id, mqtt_server, topic_sub
  client = MQTTClient(client_id, mqtt_server)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(topic_sub)
  print('Connected to %s MQTT broker, subscribed to %s topic' % (mqtt_server, topic_sub))
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.reset()

try:
  client = connect_and_subscribe()
except OSError as e:
  restart_and_reconnect()

while True:
  try:
    #client.check_msg()
    # Check for ON/OFF message
    print('Client MSG = ', client.check_msg())
    if (time.time() - last_message) > message_interval:  
 
# add current+voltage+power reading here
        client.publish(topic_pub, b'Voltage =  #%d' % 11.1)
        client.publish(topic_pub, b'Current =  #%d' % 0.50)
        client.publish(topic_pub, b'Power =  #%d' % 2199)
      else:
        pass
    
    last_message = time.time()
    counter += 1
  except OSError as e:
    restart_and_reconnect()


