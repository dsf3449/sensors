from datetime import datetime, timedelta, timezone

from sensors.common.constants import *
from sensors.domain.observation import Observation
from sensors.domain.multiobservation import MultiObservation


class Sensor:
    def __init__(self, typ, *args, **kwargs):
        self.typ = typ
        self.observed_properties = list(args)
        self.obs_func_tab = {}
        self.properties = dict(kwargs)

    def generate_observations(self,
                              phenomenon_time=None,
                              generate_phenomenon_time=lambda: datetime.now(timezone.utc).isoformat(),
                              feature_of_interest_id=None):
        """Generate observations for a given phenomenon time for all observed properties
           registered with a sensor.
        :param phenomenon_time: A string representing the phenomenon time (in ISO-format) to apply to
        all observations
        :param generate_phenomenon_time: A function that when called yields the phenomenon time as an
        ISO-formatted string to apply a given observation.  If phenomenon_time is not set,
        generate_phenomenon_time() will be used.
        :param feature_of_interest_id:
        :return: A List[Observation] of Observations created
        """
        obs = []
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


class MultiSensor:
    def __init(self, typ, multidatastream_id, *args, **kwargs):
        self.typ = typ
        self.multidatastream_id = multidatastream_id
        self.observed_property_names = list(args)
        self.properties = dict(kwargs)

    def _read_results(self):
        """ Read results from sensor

            :return: Tuple whose first element is:
                Dict of the form: Keys: observed property name (string), Value: Array of values.
            And second element:
                Dict of parameters
        """
        raise NotImplementedError

    def generate_observations(self,
                              phenomenon_time=None,
                              generate_phenomenon_time=lambda: datetime.now(timezone.utc).isoformat(),
                              feature_of_interest_id=None):
        """Generate observations for a given phenomenon time for all observed properties
           registered with a sensor.
        :param phenomenon_time: A string representing the phenomenon time (in ISO-format) to apply to
        all observations
        :param generate_phenomenon_time: A function that when called yields the phenomenon time as an
        ISO-formatted string to apply a given observation.  If phenomenon_time is not set,
        generate_phenomenon_time() will be used.
        :param feature_of_interest_id:
        :return: A List[MultiObservation] of cardinality 1
        """
        t = phenomenon_time
        if t is None:
            t = generate_phenomenon_time()
        (results_dict, parameters) = self._read_results()
        # Report results in the order expected by the MultiDatastream
        results = [results_dict[opn] for opn in self.observed_property_names]
        return [self._make_multiobservation(feature_of_interest_id, self.multidatastream_id, t, results, **parameters)]

    @staticmethod
    def _make_multiobservation(feature_of_interest_id, multidatastream_id, phenomenon_time,
                               results, **parameters):
        o = MultiObservation()
        o.featureOfInterestId = feature_of_interest_id
        o.multidatastreamId = multidatastream_id
        o.phenomenonTime = phenomenon_time
        o.results = results
        o.set_parameters(**parameters)

        return o

class OzoneSensor(Sensor):
    VALID_OBSERVED_PROPERTIES = {CFG_OBSERVED_PROPERTY_OZONE}

    def _ozone(self):
        raise NotImplementedError

    def __init__(self, typ, *args, **kwargs):
        super().__init__(typ, *args, **kwargs)

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


class AirTempRHSensor(MultiSensor):

    VALID_OBSERVED_PROPERTIES = {CFG_OBSERVED_PROPERTY_AIR_TEMP,
                                 CFG_OBSERVED_PROPERTY_RH}
    RESULT_TTL = timedelta(milliseconds=1000)

    def _read_results(self):
        raise NotImplementedError

    # def _sample(self):
    #     if self.previous_result:
    #         now = datetime.now(timezone.utc)
    #         if self.previous_result.timestamp + AirTempRHSensor.RESULT_TTL > now:
    #             return self.previous_result
    #
    #     result = self._read()
    #     self.previous_result = result
    #     return result
    #
    # def _air_temperature(self):
    #     result = self._sample()
    #     parameters = {"RH": result.humidity}
    #     return result.temperature, parameters
    #
    # def _relative_humidity(self):
    #     result = self._sample()
    #     parameters = {"T_air": result.temperature}
    #     return result.humidity, parameters

    def __init__(self, typ, *args, **kwargs):
        super().__init__(typ, *args, **kwargs)

        self.previous_result = None

        # Validate observed properties
        if len(args) != 1 and len(args) != 2:
            raise ValueError("Sensor {0} must only have one or two observed properties, but {1} were provided.".\
                             format(self.NAME, len(args)))
        # Check for duplicate definition of an observed property
        if len(args) == 2:
            if args[0].name == args[1].name:
                raise ValueError("Sensor {0} has duplicate definition of observed property {1}".\
                                 format(self.NAME, args[0].name))

        # # Register with observation generation function lookup table
        # for op in self.VALID_OBSERVED_PROPERTIES:
        #     if op == CFG_OBSERVED_PROPERTY_AIR_TEMP:
        #         self.obs_func_tab[CFG_OBSERVED_PROPERTY_AIR_TEMP] = self._air_temperature
        #     elif op == CFG_OBSERVED_PROPERTY_RH:
        #         self.obs_func_tab[CFG_OBSERVED_PROPERTY_RH] = self._relative_humidity
        for a in args:
            if a not in self.VALID_OBSERVED_PROPERTIES:
                raise ValueError("Observed property {0} is invalid.  Valid options are {1}".format(a, self.VALID_OBSERVED_PROPERTIES))

    class AirTempRHResult:
        def __init__(self, temperature, humidity):
            self.timestamp = datetime.now(timezone.utc)
            self.temperature = temperature
            self.humidity = humidity


class ParticulateMatterSensor(Sensor):
    VALID_OBSERVED_PROPERTIES = {CFG_OBSERVED_PROPERTY_PM}

    def _particulates(self):
        """
        Return tuple consisting of result, and parameters. Where:
        Result is the concentration of PM 2.5 expressed in ug/m3.
        Parameters is a dict of strings listing concentrations of
        other particle sizes (e.g. PM 1.0, PM 10.0) as well as metadata,
        which can include particle size distribution.
        :return:
        """
        raise NotImplementedError

    def __init__(self, typ, *args, **kwargs):
        super().__init__(typ, *args, **kwargs)

        # Validate observed properties
        if len(args) != 1:
            raise ValueError("Sensor {0} must only have one observed property, but {1} were provided.". \
                             format(self.NAME, len(args)))
        op = args[0]
        if op.name not in self.VALID_OBSERVED_PROPERTIES:
            raise ValueError("Sensor {0} was configured with invalid observed property {1}". \
                             format(self.NAME, op.name))

        # Register with observation generation function lookup table
        self.obs_func_tab[op.name] = self._particulates
