import os
import io
from collections import ChainMap

from .util import *
from sensors.common.constants import *
from sensors.domain.observed_property import *
from sensors.domain.thing import *
from sensors.domain import get_transport_instance

from ruamel import yaml


class Config:

    class __Config:
        def __init__(self):
            self.config = self.get_configuration()

        @classmethod
        def read_sensor_configuration(cls, yaml_path, simulator_enabled, ds_id_present, sensor):
            if simulator_enabled:
                from sensors.domain import get_sensor_instance_simulator as get_sensor_instance
            else:
                from sensors.domain import get_sensor_instance

            # Look for datastream_id at the top level of the sensor definition.  If one exists
            #   this is a MultiDatastream.  If one does not exist, this is a Datastream
            is_multi_datastream = True
            try:
                get_config_element(CFG_MULTIDATASTREAM_ID, sensor, CFG_SENSOR)
            except ConfigurationError:
                is_multi_datastream = False

            if is_multi_datastream:
                return cls._read_sensor_configuration_multidatastream(yaml_path, ds_id_present, sensor, get_sensor_instance)
            else:
                return cls._read_sensor_configuration_datastream(yaml_path, ds_id_present, sensor, get_sensor_instance)

        @classmethod
        def _read_sensor_configuration_multidatastream(cls, yaml_path, ds_id_present, sensor, get_sensor_instance):
            sensor_type = get_config_element(CFG_TYPE, sensor, CFG_SENSOR)

            return None

        @classmethod
        def _read_sensor_configuration_datastream(cls, yaml_path, ds_id_present, sensor, get_sensor_instance):
            sensor_type = get_config_element(CFG_TYPE, sensor, CFG_SENSOR)
            observed_properties = get_config_element(CFG_OBSERVED_PROPERTIES, sensor, CFG_SENSOR)
            if len(observed_properties) < 1:
                raise_config_error("No observed properties defined in sensor {0} in YAML {1}".
                                   format(str(sensor), yaml_path))
            op_objects = []
            for op in observed_properties:
                op_name = get_config_element(CFG_NAME, op, CFG_OBSERVED_PROPERTY)
                op_ds_id = get_config_element(CFG_DATASTREAM_ID, op, CFG_OBSERVED_PROPERTY)
                # Make sure this datastream_id hasn't already been encountered
                if op_ds_id in ds_id_present:
                    raise_config_error("Datastream with ID {0} is specified more than once in YAML {1}".
                                       format(op_ds_id, yaml_path))
                else:
                    ds_id_present.add(op_ds_id)
                op_objects.append(ObservedProperty(op_name, op_ds_id))
            if len(op_objects) < 1:
                raise_config_error("No valid observed properties defined in sensor {0} in YAML {1}".
                                   format(str(sensor), yaml_path))

            properties_list = get_config_element(CFG_PROPERTIES, sensor, CFG_SENSOR, optional=True)
            properties = {}
            if properties_list is not None:
                properties = ChainMap(*properties_list)

            return get_sensor_instance(sensor_type, *op_objects, **properties)

        @classmethod
        def get_configuration(cls):
            """

            :return: Dictionary representing configuration
            """
            yaml_path = os.environ.get(ENV_YAML_PATH)
            if yaml_path is None:
                raise_config_error("No configuration file defined, please make sure environment variable {0} is set".
                                   format(ENV_YAML_PATH))
            config_raw = None
            with io.open(yaml_path, 'r') as f:
                config_raw = yaml.safe_load(f)

            # First-order error checking of raw config
            if config_raw is None:
                raise_config_error("Unable to parse configuration in YAML {0}.".format(yaml_path))
            if CFG_THING not in config_raw:
                raise_config_error("Element {0} not configured in YAML {1}.".format(CFG_THING,
                                                                                    yaml_path))
            if CFG_SENSORS not in config_raw:
                raise_config_error("Element {0} not configured in YAML {1}.".
                                   format(CFG_SENSORS, yaml_path))
            sensors = config_raw[CFG_SENSORS]
            if type(sensors) != list:
                raise_config_error("Element {0} with value {1} is invalid in YAML {2}.".
                                   format(CFG_SENSORS, str(sensors), yaml_path))
            if len(sensors) < 1:
                raise_config_error("Element {0} not configured in YAML {1}.".format(CFG_SENSORS,
                                                                                    yaml_path))
            if CFG_TRANSPORTS not in config_raw:
                raise_config_error("Element {0} not configured in YAML {1}.".format(CFG_TRANSPORTS,
                                                                                    yaml_path))
            transports = config_raw[CFG_TRANSPORTS]
            if type(transports) != list:
                raise_config_error("Element {0} with value {1} is invalid in YAML {2}.".
                                   format(CFG_TRANSPORTS, str(transports), yaml_path))

            # Convert raw config elements to ones easier to deal with (doing
            # validation along the way).
            ds_id_present = set()
            c = {}

            # Simulator
            simulator_enabled = False
            if CFG_SIMULATOR in config_raw:
                simulator_enabled = get_config_element(CFG_ENABLED, config_raw[CFG_SIMULATOR], CFG_SIMULATOR,
                                                       optional=True)
                if simulator_enabled is None:
                    simulator_enabled = False
            c[CFG_SIMULATOR] = simulator_enabled

            # Logging
            logger_path = DEFAULT_LOGGER_PATH
            if CFG_LOGGING in config_raw:
                logging_cfg = config_raw[CFG_LOGGING]
                # Logging file path
                logger_path = get_config_element_with_default(CFG_LOGGING_LOGGER_PATH, logging_cfg,
                                                              default=DEFAULT_LOGGER_PATH)
                # Logging levels
                # Console logger
                level_console = get_config_element_with_default(CFG_LOGGING_LEVEL_CONSOLE, logging_cfg,
                                                                default=DEFAULT_LOGGER_LEVEL_CONSOLE)
                if level_console not in CFG_LOGGING_LEVELS:
                    raise_config_error("Console logging level {0} is not known.".format(level_console))
                c[CFG_LOGGING_LEVEL_CONSOLE] = CFG_LOGGING_LEVELS[level_console]
                # File logger
                level_file = get_config_element_with_default(CFG_LOGGING_LEVEL_FILE, logging_cfg,
                                                             default=DEFAULT_LOGGER_LEVEL_FILE)
                if level_file not in CFG_LOGGING_LEVELS:
                    raise_config_error("File logging level {0} is not known.".format(level_file))
                c[CFG_LOGGING_LEVEL_FILE] = CFG_LOGGING_LEVELS[level_file]

            # Validate logging path
            logger_path_dir = os.path.dirname(logger_path)
            if not os.path.exists(logger_path_dir):
                raise raise_config_error("Logger path directory {0} does not exist.".format(logger_path_dir))
            c[CFG_LOGGING_LOGGER_PATH] = logger_path

            # Spooler
            db_path = DEFAULT_DB_PATH
            if CFG_SPOOLER in config_raw:
                db_path = get_config_element(CFG_SPOOLER_DB_PATH, config_raw[CFG_SPOOLER], CFG_SPOOLER,
                                             optional=True)
                if db_path is None:
                    db_path = DEFAULT_DB_PATH
            db_path_dir = os.path.dirname(db_path)
            if not os.path.exists(db_path_dir):
                raise raise_config_error("Spooler path directory {0} does not exist.".format(db_path_dir))
            c[CFG_SPOOLER_DB_PATH] = db_path

            # Thing
            thing_id = get_config_element(CFG_ID, config_raw[CFG_THING], CFG_THING)
            foi_id = get_config_element(CFG_LOCATION_ID, config_raw[CFG_THING], CFG_THING)
            c[CFG_THING] = Thing(thing_id, foi_id)

            # Sensors
            sensor_objects = []
            for s in sensors:
                sensor_objects.append(cls.read_sensor_configuration(yaml_path, simulator_enabled, ds_id_present, s))

            if len(sensor_objects) < 1:
                raise_config_error("No valid sensors defined in YAML {0}".format(yaml_path))

            c[CFG_SENSORS] = sensor_objects

            # Transports
            transport_present = set()
            transport_objects = []
            for t in transports:
                transport_type = get_config_element(CFG_TYPE, t, CFG_TRANSPORT)
                properties = get_config_element(CFG_PROPERTIES, t, CFG_TRANSPORT)
                if len(properties) < 1:
                    raise_config_error("No properties defined in transport with type {0} in YAML {1}".
                                       format(transport_type, yaml_path))
                transport_object = get_transport_instance(transport_type, **properties)
                t_identifier = transport_object.identifier()
                if t_identifier in transport_present:
                    raise_config_error("Transport with identifier {0} is specified more than once in YAML {1}".
                                       format(t_identifier, yaml_path))
                else:
                    transport_present.add(t_identifier)
                transport_objects.append(transport_object)

            if len(transport_objects) < 1:
                raise_config_error("No valid transports defined in YAML {0}".format(yaml_path))

            c[CFG_TRANSPORTS] = transport_objects

            return c

        def __str__(self):
            return repr(self) + str(self.config)

    instance = None

    def __init__(self, unittest=False):
        if not Config.instance or unittest:
            Config.instance = Config.__Config()
        else:
            pass

    def __getattr__(self, item):
        return getattr(self.instance, item)
