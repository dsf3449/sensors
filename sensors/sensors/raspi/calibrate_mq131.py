import argparse

import RPi.GPIO as GPIO

from sensors.common.constants import CFG_SENSOR_ADC_MCP3002
from sensors.common.constants import CFG_SENSOR_ADC_ADS1015
from sensors.domain import get_sensor_instance
from sensors.domain.observed_property import ObservedProperty


DEFAULT_ADC = CFG_SENSOR_ADC_MCP3002
VALID_ADC = [CFG_SENSOR_ADC_MCP3002, CFG_SENSOR_ADC_ADS1015]


def main():
    parser = argparse.ArgumentParser(description='Calibrate Ro value for MQ131 sensor')
    parser.add_argument('-a', '--adc', default=DEFAULT_ADC, choices=VALID_ADC)
    args = parser.parse_args()

    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        print("Calibrating MQ131 sensor (this will take about 30 seconds)...")
        properties = {'adc': args.adc}
        instance = get_sensor_instance("mq131", ObservedProperty("ozone", "dummmydatastreamid"),
                                       **properties)
        result = instance.calibrate_Ro()
        print("Ro value for MQ131 sensor is {0}".format(result))
    except KeyboardInterrupt:
        GPIO.cleanup()
