import RPi.GPIO as GPIO
import DHT11_Python.dht11 as dht11

# initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()

# read data using pin 14
instance = dht11.DHT11(pin=17)
result = instance.read()

if result.is_valid():
    print("Temperature: %d C" % result.temperature)
    print ("Temperature: %d F" % result.temperature * 1.8 + 32)
    print("Humidity: %d %%" % result.humidity)
else:
    print("Error: %d" % result.error_code)

