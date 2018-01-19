from typing import List
from datetime import datetime

from sensors.config.constants import *
from sensors.domain.observation import Observation


class Sensor:
    def __init__(self, typ, *args):
        self.typ = typ
        self.observed_properties = list(args)
        self.obs_func_tab = {}

    def generate_observations(self,
                              phenomenon_time=None,
                              generate_phenomenon_time=lambda: datetime.now().isoformat(),
                              feature_of_interest_id=None):
        """Generate observations for a given phenomenon time for all observed properties
           registered with a sensor.
        :param phenomenon_time: A string representing the phenomenon time (in ISO-format) to apply to
        all observations
        :param generate_phenomenon_time: A function that when called yields the phenomenon time as an
        ISO-formatted string to apply a given observation.  If phenomenon_time is not set,
        generate_phenomenon_time() will be used.
        :param datastream_id:
        :param feature_of_interest_id:
        :return: A List[Observation] of Observations created
        """
        obs: List[Observation] = []
        for op in self.observed_properties:
            generate_observation = self.obs_func_tab[op.name]
            t = phenomenon_time
            if t is None:
                t = generate_phenomenon_time()
            (result, parameters) = generate_observation()
            o = self._make_observation(feature_of_interest_id, op.datastream_id, t, result, **parameters)
            obs.append(o)
        return obs

    @staticmethod
    def _make_observation(feature_of_interest_id, datastream_id, phenomenon_time,
                          result, **parameters):
        o = Observation()
        o.featureOfInterestId = feature_of_interest_id
        o.datastreamId = datastream_id
        o.phenomenonTime = phenomenon_time
        o.result = result
        o.set_parameters(**parameters)

        return o


class OzoneSensor(Sensor):
    VALID_OBSERVED_PROPERTIES = {CFG_OBSERVED_PROPERTY_OZONE}

    def _ozone(self):
        raise NotImplementedError

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


class AirTempRHSensor(Sensor):
    VALID_OBSERVED_PROPERTIES = {CFG_OBSERVED_PROPERTY_AIR_TEMP,
                                 CFG_OBSERVED_PROPERTY_RH}

    def _air_temperature(self):
        raise NotImplementedError

    def _relative_humidity(self):
        raise NotImplementedError

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
        for op in self.VALID_OBSERVED_PROPERTIES:
            if op == CFG_OBSERVED_PROPERTY_AIR_TEMP:
                self.obs_func_tab[CFG_OBSERVED_PROPERTY_AIR_TEMP] = self._air_temperature
            elif op == CFG_OBSERVED_PROPERTY_RH:
                self.obs_func_tab[CFG_OBSERVED_PROPERTY_RH] = self._relative_humidity
