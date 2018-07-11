import random

from sensors.domain.sensor import ParticulateMatterSensor
from sensors.common.constants import *


class Sen0177(ParticulateMatterSensor):
    NAME = CFG_SENSOR_TYPE_SEN0177

    def _particulates(self):
        result = random.gauss(56.0, 5.6)
        pm1 = random.gauss(41.0, 4.1)
        pm10 = random.gauss(61, 6.1)
        parameters = {"pm1": str(pm1),
                      "pm10": str(pm10)}
        return result, parameters

    def __init__(self, typ, *args, **kwargs):
        super().__init__(typ, *args, **kwargs)
