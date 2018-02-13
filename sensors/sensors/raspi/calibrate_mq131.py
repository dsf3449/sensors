import RPi.GPIO as GPIO

from sensors.domain import get_sensor_instance
from sensors.domain.observed_property import ObservedProperty

def main():
    # initialize GPIO
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()

    print("Calibrating MQ131 sensor (this will take about 30 seconds)...")
    instance = get_sensor_instance("mq131", ObservedProperty("ozone", "dummmydatastreamid"))
    result = instance._measure_Ro()
    print("Ro value for MQ131 sensor is {0}".format(result))
