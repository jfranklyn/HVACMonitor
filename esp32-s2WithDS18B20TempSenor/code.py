"""
Main code for MQTT client to control the ESP-32 S2 Feather S2 and
Adafruit DS18D20 waterproof temperature sensor
relayMQTT topic = hvac-monitor
Using io.adafruit.com dashboard to display the output the sensors
An RPI Zero W is used as the MQTT broker. The RPI sends messages to io.adafruit
"""
import gc
# import ipaddress
# import os
# import ssl
import time
import board

from adafruit_onewire.bus import OneWireBus
from adafruit_ds18x20 import DS18X20
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import socketpool
import wifi
import supervisor
import feathers2

# globals
keep_alive = 60
QOS1 = 1
QOS2 = 0
CLEAN_SESSION = False
port = 1883
last_message = 0
message_interval = 30  # seconds

# Make sure the 2nd LDO is turned on
feathers2.enable_LDO2(True)

# added code to publish sensor connection status
client_id = 'supplyairtemperature'
will_status_topic = 'last-will/connected/' + client_id
topic_pub_ret_air_temp = 'hvac-monitor/supplyair/temperature'

# I2C connection for Adafruit DS18D20
try:
    # Initialize one-wire bus on board pin D11.
    ow_bus = OneWireBus(board.D11)

    # Scan for sensors and grab the first one found.
    global ds18
    ds18 = DS18X20(ow_bus, ow_bus.scan()[0])
    ds18.resolution = 12
except Exception as ds18b20_err:
    print('DS18B20 exception {}'.format(ds18b20_err))

# Make sure the 2nd LDO is turned on
feathers2.enable_LDO2(True)

# Turn on the internal blue LED
feathers2.led_set(True)

# Show available memory
print("Memory Info - gc.mem_free()")
print("---------------------------")
print("{} Bytes\n".format(gc.mem_free()))

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError as imp_err:
    print("WiFi secrets are kept in secrets.py, error {}".format(imp_err))
    raise

print("Connecting to %s" % secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!" % secrets["ssid"])
print("My IP address is", wifi.radio.ipv4_address)


def on_disconnect(client, userdata, flags, rc=0):
    m = "DisConnected flags" + "result code " + str(rc)
    print(m)
    client.connected_flag = False
    mqtt_client.publish(will_status_topic, 0, qos=2, retain=True)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("connected OK Returned code=", rc)
        client.connected_flag = True  # Flag to indicate success
    else:
        print("Bad connection Returned code=", rc)
        client.bad_connection_flag = True


def on_log(client, userdata, level, buf):
    print("log: ", buf)


def on_message(client, userdata, message):
    print("message received  ", str(message.payload.decode("utf-8")))


def connect_mqtt():
    # Create a socket pool
    pool = socketpool.SocketPool(wifi.radio)

    # Set up a MiniMQTT Client
    mqtt_client = MQTT.MQTT(
        broker=secrets["mqtt_broker"],
        port=port,
        socket_pool=pool,
        ssl_context=None,
    )

    # Setup the callback methods above
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message

    # Connect the client to the MQTT broker.
    print("Connecting to MQTT Broker...")
    # set will message to track status of client disconnects
    mqtt_client.will_set(will_status_topic, time.time(), 2, True)

    try:
        mqtt_client.connect()
        print('mqtt client status = ', mqtt_client.is_connected())
    except Exception as sensor_err:
        return 'mqtt_client not connected'

    mqtt_client.publish(will_status_topic, 1, 2, True)
    mqtt_client.connected_flag = False  # create flags
    mqtt_client.bad_connection_flag = False  #
    mqtt_client.retry_count = 0  #

    return mqtt_client


"""
this function will try to reconnect to the mqtt broker. If it can't it does a soft-reset of the ESP-32
"""


def restart_and_reconnect():
    print('Failed to connect to MQTT broker. Reconnecting...')
    try:
        mqtt_client.reconnect()
        if mqtt_client.is_connected():
            # msg = 'Sensor ' + client_id + ' Re-Connected'
            mqtt_client.publish(will_status_topic, 1, 2, True)
    except Exception as sensor_err:
        time.sleep(10)
        # msg = 'Sensor ' + client_id + ' Disconnected'
        mqtt_client.publish(will_status_topic, 0, 2, True)

        # soft-reset esp32-s2
        supervisor.reload()
        return 'mqtt_client not connected'


"""
Read temperature from the DS18B20 sensor
"""


def read_sensor():
    try:
        conversion_delay = ds18.start_temperature_read()
        conversion_ready_at = time.monotonic() + conversion_delay
        print("waiting", end="")
        while time.monotonic() < conversion_ready_at:
            print(".", end="")
            time.sleep(0.1)
        print("\nTemperature: {0:0.3f}C\n".format(ds18.read_temperature()))

    except Exception as sensor_err:
        print('DS18B20 sensor offline reason {}'.format(sensor_err))
        mqtt_client.publish(will_status_topic, 0, 2, True)

    return '%4.2f' % ds18.read_temperature()


try:
    mqtt_client = connect_mqtt()
except Exception as e:
    print('MQTT connect exception ', e)
    restart_and_reconnect()

while True:
    mqtt_client.loop()
    try:
        if (time.time() - last_message) > message_interval:
            feathers2.led_blink()
            # ambient temperature is probably not important as it will be around 120+ in any attic
            obj_temp_f = read_sensor()
            print('published msg ', (topic_pub_ret_air_temp + ' ' + obj_temp_f))
            # add the topics and the sensor reading to the published msg
            mqtt_client.publish(topic_pub_ret_air_temp, (topic_pub_ret_air_temp + ' ' + obj_temp_f))
            last_message = time.time()
    except Exception as while_err:
        print('Main loop Exception Error ', while_err)
        restart_and_reconnect()
