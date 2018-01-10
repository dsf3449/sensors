import os
import io
import logging

from sensors.config.constants import *
from sensors.domain.observed_property import *
from sensors.domain.sensor import *
from sensors.domain.thing import *
from sensors.domain.transport import *

from ruamel import yaml


class ConfigurationError(Exception):
    """Exception raised for errors in config_rawuration

    """

    def __init__(self, message):
        self.message = message


def load_config():
    yaml_path = os.environ.get(ENV_YAML_PATH)
    config_raw = None
    with io.open(yaml_path, 'r') as f:
        config_raw = yaml.safe_load(f)

    # First-order error checking of raw config
    if config_raw is None:
        mesg = "Unable to parse configuration in YAML {0}.".format(yaml_path)
        logging.error(mesg)
        raise ConfigurationError(mesg)
    if CFG_THING not in config_raw:
        mesg = "Element {0} not configured in YAML {1}.".format(CFG_THING,
                                                                    yaml_path)
        logging.error(mesg)
        raise ConfigurationError(mesg)
    if CFG_SENSORS not in config_raw:
        mesg = "Element {0} not configured in YAML {1}.".format(CFG_SENSORS,
                                                                    yaml_path)
        logging.error(mesg)
        raise ConfigurationError(mesg)
    sensors = config_raw[CFG_SENSORS]
    if type(sensors) != list:
        mesg = "Element {0} with value {1} is invalid in YAML {2}.".format(CFG_SENSORS,
                                                                           str(sensors),
                                                                           yaml_path)
        logging.error(mesg)
        raise ConfigurationError(mesg)
    if len(sensors) < 1:
        mesg = "Element {0} not configured in YAML {1}.".format(CFG_SENSORS,
                                                                    yaml_path)
        logging.error(mesg)
        raise ConfigurationError(mesg)
    if CFG_TRANSPORTS not in config_raw:
        mesg = "Element {0} not configured in YAML {1}.".format(CFG_TRANSPORTS,
                                                                    yaml_path)
        logging.error(mesg)
        raise ConfigurationError(mesg)
    transports = config_raw[CFG_TRANSPORTS]
    if type(transports) != list:
        mesg = "Element {0} with value {1} is invalid in YAML {2}.".format(CFG_TRANSPORTS,
                                                                           str(transports),
                                                                           yaml_path)
        logging.error(mesg)
        raise ConfigurationError(mesg)

    # Convert raw config elements to ones easier to deal with (doing
    # validation along the way).
    c = {}
    # Thing
    foi_id = get_config_element(CFG_FOI_ID, config_raw[CFG_THING], CFG_THING)
    c[CFG_THING] = Thing(foi_id)

    # Sensors
    sensor_objects = []
    for s in sensors:
        sensor_name = get_config_element(CFG_NAME, s, CFG_SENSOR)
        observed_properties = get_config_element(CFG_OBSERVED_PROPERTIES, s, CFG_SENSOR)
        if len(observed_properties) < 1:
            mesg = "No observed properties defined in sensor {0} in YAML {1}".\
                format(str(s), yaml_path)
            logging.error(mesg)
            raise ConfigurationError(mesg)
        op_objects = []
        for op in observed_properties:
            op_name = get_config_element(CFG_NAME, op, CFG_OBSERVED_PROPERTY)
            op_ds_id = get_config_element(CFG_DATASTREAM_ID, op, CFG_OBSERVED_PROPERTY)
            op_objects.append(ObservedProperty(op_name, op_ds_id))
        if len(op_objects) < 1:
            mesg = "No valid observed properties defined in sensor {0} in YAML {1}".\
                format(str(s), yaml_path)
            logging.error(mesg)
            raise ConfigurationError(mesg)
        sensor_objects.append(Sensor(sensor_name, op_objects))

    if len(sensor_objects) < 1:
        mesg = "No valid sensors defined in YAML {0}".format(yaml_path)
        logging.error(mesg)
        raise ConfigurationError(mesg)

    c[CFG_SENSORS] = sensor_objects

    # Transports
    transport_objects = []
    for t in transports:
        transport_name = get_config_element(CFG_NAME, t, CFG_TRANSPORT)
        properties = get_config_element(CFG_PROPERTIES, t, CFG_TRANSPORT)
        if len(properties) < 1:
            mesg = "No properties defined in transport with name {0} in YAML {1}".\
                format(transport_name, yaml_path)
            logging.error(mesg)
            raise ConfigurationError(mesg)
        transport_objects.append(Transport.get_instance(transport_name, **properties))

    if len(transport_objects) < 1:
        mesg = "No valid transports defined in YAML {0}".format(yaml_path)
        logging.error(mesg)
        raise ConfigurationError(mesg)

    c[CFG_TRANSPORTS] = transport_objects

    return c


def get_config_element(element_name, container, container_name):
    if element_name not in container:
        mesg = "{container_name} {container} does not contain element {element_name}".\
            format(container_name=container_name, container=str(container),
                   element_name=element_name)
        logging.error(mesg)
        raise ConfigurationError(mesg)
    return container[element_name]
