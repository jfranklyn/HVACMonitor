# HVACMonitor
HVAC monitoring system using ESP8266 micro controllers and Adafruit sensors
# hvacMQTT.py - Monitors a Mosquitto MQTT queue for hvac events
# from an array of sensors, detects critical changes in those
# sensor values, and injects alarms into an io.adafruit.com queue to update the dashboard.
# DS8266 HUZZAH WiFi are used as the micro-processor clients
# RPI Zero W used as the MQTT Broker/server and to update the io.adafruit.com dashboard
# sensors include DS18B20 - 1-wire temperature sensor
# Relay Featherwing
# INA260 - DC/Current/Power monitor
# MLX90614 3V - infrared temperature sensor
# All sensors purchased from Adafruit
