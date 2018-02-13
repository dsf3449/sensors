import RPi.GPIO as GPIO

from sensors.domain import get_sensor_instance

def main():
    # initialize GPIO
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()

    instance = get_sensor_instance("mq131", [])
    result = instance._measure_Ro()
    print("Ro value for MQ131 sensor is {0}".format(result))
