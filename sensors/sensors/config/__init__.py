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
        raise_config_error("Unable to parse configuration in YAML {0}.".format(yaml_path))
    if CFG_THING not in config_raw:
        raise_config_error("Element {0} not configured in YAML {1}.".format(CFG_THING,
                                                                            yaml_path))
    if CFG_SENSORS not in config_raw:
        raise_config_error("Element {0} not configured in YAML {1}.".\
                           format(CFG_SENSORS, yaml_path))
    sensors = config_raw[CFG_SENSORS]
    if type(sensors) != list:
        raise_config_error("Element {0} with value {1} is invalid in YAML {2}.".\
                           format(CFG_SENSORS, str(sensors), yaml_path))
    if len(sensors) < 1:
        raise_config_error("Element {0} not configured in YAML {1}.".format(CFG_SENSORS,
                                                                            yaml_path))
    if CFG_TRANSPORTS not in config_raw:
        raise_config_error("Element {0} not configured in YAML {1}.".format(CFG_TRANSPORTS,
                                                                            yaml_path))
    transports = config_raw[CFG_TRANSPORTS]
    if type(transports) != list:
        raise_config_error("Element {0} with value {1} is invalid in YAML {2}.".\
                           format(CFG_TRANSPORTS, str(transports), yaml_path))

    # Convert raw config elements to ones easier to deal with (doing
    # validation along the way).
    ds_id_present = set()
    c = {}
    # Thing
    thing_id = get_config_element(CFG_ID, config_raw[CFG_THING], CFG_THING)
    foi_id = get_config_element(CFG_LOCATION_ID, config_raw[CFG_THING], CFG_THING)
    c[CFG_THING] = Thing(thing_id, foi_id)

    # Sensors
    sensor_objects = []
    for s in sensors:
        sensor_type = get_config_element(CFG_TYPE, s, CFG_SENSOR)
        observed_properties = get_config_element(CFG_OBSERVED_PROPERTIES, s, CFG_SENSOR)
        if len(observed_properties) < 1:
            raise_config_error("No observed properties defined in sensor {0} in YAML {1}".\
                format(str(s), yaml_path))
        op_objects = []
        for op in observed_properties:
            op_name = get_config_element(CFG_NAME, op, CFG_OBSERVED_PROPERTY)
            op_ds_id = get_config_element(CFG_DATASTREAM_ID, op, CFG_OBSERVED_PROPERTY)
            # Make sure this datastream_id hasn't already been encountered
            if op_ds_id in ds_id_present:
                raise_config_error("Datastream with ID {0} is specified more than once in YAML {1}".\
                                   format(op_ds_id, yaml_path))
            else:
                ds_id_present.add(op_ds_id)
            op_objects.append(ObservedProperty(op_name, op_ds_id))
        if len(op_objects) < 1:
            raise_config_error("No valid observed properties defined in sensor {0} in YAML {1}".\
                format(str(s), yaml_path))
        sensor_objects.append(Sensor(sensor_type, *op_objects))

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
            raise_config_error("No properties defined in transport with type {0} in YAML {1}".\
                format(transport_type, yaml_path))
        transport_object = Transport.get_instance(transport_type, **properties)
        t_identifier = transport_object.identifier()
        if t_identifier in transport_present:
            raise_config_error("Transport with identifier {0} is specified more than once in YAML {1}". \
                format(t_identifier, yaml_path))
        else:
            transport_present.add(t_identifier)
        transport_objects.append(transport_object)

    if len(transport_objects) < 1:
        raise_config_error("No valid transports defined in YAML {0}".format(yaml_path))

    c[CFG_TRANSPORTS] = transport_objects

    return c


def get_config_element(element_name, container, container_name, optional=False):
    element = None
    if (element_name not in container) and optional is False:
        mesg = "{container_name} {container} does not contain element {element_name}".\
            format(container_name=container_name, container=str(container),
                   element_name=element_name)
        logging.error(mesg)
        raise ConfigurationError(mesg)
    else:
        element = container[element_name]
    return element


def raise_config_error(mesg: str):
    logging.error(mesg)
    raise ConfigurationError(mesg)
