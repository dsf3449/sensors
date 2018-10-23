import random

from sensors.domain.sensor import ParticulateMatterSensor
from sensors.common.constants import *


class Sen0177(ParticulateMatterSensor):
    NAME = CFG_SENSOR_TYPE_SEN0177

    def _read_results(self):
        pm1 = random.gauss(41.0, 4.1)
        pm25 = random.gauss(56.0, 5.6)
        pm10 = random.gauss(61, 6.1)
        results = {CFG_OBSERVED_PROPERTY_PM1: pm1,
                   CFG_OBSERVED_PROPERTY_PM25: pm25,
                   CFG_OBSERVED_PROPERTY_PM10: pm10}
        parameters = {}
        return results, parameters

    def __init__(self, typ, *args, **kwargs):
        super().__init__(typ, *args, **kwargs)
