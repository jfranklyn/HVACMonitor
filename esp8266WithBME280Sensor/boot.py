'''
Main boot file used to initialize WiFi
'''
import micropython
import network
import machine
import gc
gc.collect()

try:
    from secrets import secrets
except ImportError as imp_err:
    print("WiFi secrets are kept in secrets.py, error {}".format(imp_err))
    raise
    
station = network.WLAN(network.STA_IF)

station.active(True)
station.connect(secrets["ssid"], secrets["password"])

while station.isconnected() == False:
  pass

print('Connection successful')
print(station.ifconfig())
