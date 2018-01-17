import random

from sensors.domain.sensor import OzoneSensor
from sensors.config.constants import *


class Mq131(OzoneSensor):
    NAME = CFG_SENSOR_TYPE_MQ131

    def _ozone(self):
        result = random.uniform(1.23, 123.45)
        parameters = {"voltage": str(random.uniform(1.23, 123.45)),
                      "Rs": str(random.uniform(1.23, 123.45)),
                      "Ro": str(random.uniform(1.23, 123.45)),
                      "Rs_Ro_Ratio": str(random.uniform(1.23, 123.45))}
        return result, parameters

    VALID_OBSERVED_PROPERTIES = {CFG_OBSERVED_PROPERTY_OZONE}

    def __init__(self, typ, *args):
        super().__init__(typ, *args)
