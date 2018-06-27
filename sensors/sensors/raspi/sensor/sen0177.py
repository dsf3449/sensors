
from sensors.domain.sensor import ParticulateMatterSensor
from sensors.common.constants import *


class Sen0177(ParticulateMatterSensor):
    NAME = CFG_SENSOR_TYPE_SEN0177

    def _particulates(self):
        pass

    def __init__(self, typ, *args, **kwargs):
        super().__init__(typ, *args, **kwargs)
