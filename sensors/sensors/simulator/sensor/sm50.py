import random

from sensors.domain.sensor import OzoneSensor
from sensors.common.constants import *


class Sm50(OzoneSensor):
    NAME = CFG_SENSOR_TYPE_SM50

    def _ozone(self):
        result = random.uniform(0.001, 0.5)
        parameters = {"adc_avg": str(random(0, 255))}
        return result, parameters

    def __init__(self, typ, *args, **kwargs):
        super().__init__(typ, *args, **kwargs)
