import logging

from sensors.config.constants import *


class Transport:
    TRANSPORT_NAME_HTTPS = CFG_TRANSPORT_NAME_HTTPS

    def __init__(self, name, **kwargs):
        self.name = name
        self.properties = dict(kwargs)

    @classmethod
    def get_instance(cls, name, **kwargs):
        if name == Transport.TRANSPORT_NAME_HTTPS:
            return HttpsTransport(name, **kwargs)
        else:
            mesg = "Unknown transport {0}".format(name)
            logging.error(mesg)
            raise ValueError(mesg)

class HttpsTransport(Transport):
    """HTTPS transport with JWT authentication

    """
    def __init__(self, name, **kwargs):
        # Make sure required elements are present
        get_config_element(CFG_TRANSPORT_HTTPS_AUTH_URL,
                           kwargs, CFG_PROPERTIES)
        get_config_element(CFG_URL,
                           kwargs, CFG_PROPERTIES)
        get_config_element(CFG_TRANSPORT_HTTPS_JWT_ID,
                           kwargs, CFG_PROPERTIES)
        get_config_element(CFG_TRANSPORT_HTTPS_JWT_KEY,
                           kwargs, CFG_PROPERTIES)
        Transport.__init__(self, name, **kwargs)


def get_config_element(element_name, container, container_name):
    if element_name not in container:
        mesg = "{container_name} {container} does not contain element {element_name}".\
            format(container_name=container_name, container=str(container),
                   element_name=element_name)
        logging.error(mesg)
        raise Exception(mesg)
    return container[element_name]
