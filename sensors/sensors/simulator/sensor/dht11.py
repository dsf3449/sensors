import datetime
import random

from sensors.domain.sensor import AirTempRHSensor
from sensors.common.constants import *


class Dht11(AirTempRHSensor):
    NAME = CFG_SENSOR_TYPE_DHT11

    def _read_results(self):
        t = random.uniform(1.23, 123.45)
        rh = random.uniform(15.0, 99.99)
        results = {CFG_OBSERVED_PROPERTY_AIR_TEMP: t,
                   CFG_OBSERVED_PROPERTY_RH: rh}
        parameters = None
        return results, parameters

    def __init__(self, typ, *args, **kwargs):
        super().__init__(typ, *args, **kwargs)
