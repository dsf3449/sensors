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
    def __init__(self, typ, *args, **kwargs):
        self.typ = typ
        self.multidatastream_id = args[0]
        self.observed_property_names = list(args[1:])
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

    def __init__(self, typ, *args, **kwargs):
        super().__init__(typ, *args, **kwargs)

        self.previous_result = None

        # Validate observed property names
        if len(self.observed_property_names) != 1 and len(self.observed_property_names) != 2:
            raise ValueError("Sensor {0} must only have one or two observed properties, but {1} were provided.".\
                             format(self.NAME, len(self.observed_property_names)))
        # Check for duplicate definition of an observed property
        if len(self.observed_property_names) == 2:
            if self.observed_property_names[0] == self.observed_property_names[1]:
                raise ValueError("Sensor {0} has duplicate definition of observed property {1}".\
                                 format(self.NAME, self.observed_property_names[0].name))

        for opn in self.observed_property_names:
            if opn not in self.VALID_OBSERVED_PROPERTIES:
                raise ValueError("Observed property {0} is invalid.  Valid options are {1}".format(opn,
                                                                                                   self.VALID_OBSERVED_PROPERTIES))

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
