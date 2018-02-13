import datetime
import time

import RPi.GPIO as GPIO

import sensors.raspi.dht11 as dht11

def main():
    # initialize GPIO
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()

    # read data using pin 14
    instance = dht11.DHT11(pin=17)
    result = instance.read()

    if result.is_valid():
        print("Last valid input: {0}".format(str(datetime.datetime.now())))
        print ("Temperature: {0:.2f} C".format(result.temperature))
        temp_f = result.temperature * 1.8 + 32.0
        print ("Temperature: {0:.2f} F".format(temp_f))
        print("Humidity: {0:.2f}%".format(result.humidity))
    else:
        print("Error: {0}".format(result.error_code))

    time.sleep(1)
