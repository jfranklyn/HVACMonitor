'''
Main code for MQTT client to control the ESP8266 and 
DS18B20 1-wire waterproof temperature sensor
relayMQTT topic = hvac-monitor
Using io.adafruit.com dashboard to control the sensors
'''

def sub_cb(topic, msg):
  print((topic, msg))
  if topic == b'hvac-monitor' and msg == b'received':
    print('ESP8266 Relay received hello message')

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
      if (client.check_msg == 'ON'):
        print('Received ON msg')
# add 1-wire temperature reading here
        client.publish(topic_pub, b'Received ON #%d' % counter)
      else:
        pass
    
    last_message = time.time()
    counter += 1
  except OSError as e:
    restart_and_reconnect()

