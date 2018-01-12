import random

from sensors.domain.sensor import Sensor
from sensors.config.constants import *


class Dht11(Sensor):
    NAME = CFG_SENSOR_TYPE_DHT11

    def _air_temperature(self):
        result = random.uniform(1.23, 123.45)
        parameters = {"Relative humidity": str(random.uniform(15.0, 99.99))}
        return result, parameters

    def _relative_humidity(self):
        result = random.uniform(15.0, 99.99)
        parameters = {"Air temperature": str(random.uniform(1.23, 123.45))}
        return result, parameters

    VALID_OBSERVED_PROPERTIES = {CFG_OBSERVED_PROPERTY_AIR_TEMP: _air_temperature,
                                 CFG_OBSERVED_PROPERTY_RH: _relative_humidity}

    def __init__(self, typ, *args):
        super().__init__(typ, *args)

        # Validate observed properties
        if len(args) != 1 and len(args) != 2:
            raise ValueError("Sensor {0} must only have one or two observed properties, but {1} were provided.".\
                             format(self.NAME, len(args)))
        # Check for duplicate definition of an observed property
        if len(args) == 2:
            if args[0].name == args[1].name:
                raise ValueError("Sensor {0} has duplicate definition of observed property {1}".\
                                 format(self.NAME, args[0].name))

        # Register with observation generation function lookup table
        self.obs_func_tab.update(self.VALID_OBSERVED_PROPERTIES)
