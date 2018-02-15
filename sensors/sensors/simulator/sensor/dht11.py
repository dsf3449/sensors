import datetime
import random

from sensors.domain.sensor import AirTempRHSensor
from sensors.config.constants import *


class Dht11(AirTempRHSensor):
    NAME = CFG_SENSOR_TYPE_DHT11

    def _read(self):
        t = random.uniform(1.23, 123.45)
        rh = random.uniform(15.0, 99.99)
        return AirTempRHSensor.AirTempRHResult(t, rh)

    def __init__(self, typ, *args, **kwargs):
        super().__init__(typ, *args, **kwargs)
