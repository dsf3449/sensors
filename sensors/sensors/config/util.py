import logging

class ConfigurationError(Exception):
    """Exception raised for errors in configuration

    """

    def __init__(self, message):
        self.message = message


def raise_config_error(mesg: str, logger: logging.Logger=None):
    if logger:
        logger.error(mesg)
    raise ConfigurationError(mesg)


def get_config_element(element_name, container, container_name, optional=False):
    element = None
    if (element_name not in container) and optional is False:
        raise_config_error("{container_name} {container} does not contain element {element_name}".\
                           format(container_name=container_name, container=str(container),
                           element_name=element_name))
    elif element_name in container:
        element = container[element_name]
    return element


def get_config_element_with_default(element_name, container, default=None):
    element = None
    if element_name not in container:
        element = default
    else:
        element = container[element_name]
    return element
