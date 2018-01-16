import random

from sensors.domain.sensor import Sensor
from sensors.config.constants import *


class Mq131(Sensor):
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

        # Validate observed properties
        if len(args) != 1:
            raise ValueError("Sensor {0} must only have one observed property, but {1} were provided.".\
                             format(self.NAME, len(args)))
        op = args[0]
        if op.name not in self.VALID_OBSERVED_PROPERTIES:
            raise ValueError("Sensor {0} was configured with invalid observed property {1}".\
                             format(self.NAME, op.name))

        # Register with observation generation function lookup table
        self.obs_func_tab[op.name] = self._ozone
