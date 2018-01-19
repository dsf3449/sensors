import random

from sensors.domain.sensor import AirTempRHSensor
from sensors.config.constants import *


class Dht11(AirTempRHSensor):
    NAME = CFG_SENSOR_TYPE_DHT11

    def _air_temperature(self):
        result = random.uniform(1.23, 123.45)
        parameters = {"Relative humidity": str(random.uniform(15.0, 99.99))}
        return result, parameters

    def _relative_humidity(self):
        result = random.uniform(15.0, 99.99)
        parameters = {"Air temperature": str(random.uniform(1.23, 123.45))}
        return result, parameters

    def __init__(self, typ, *args):
        super().__init__(typ, *args)
