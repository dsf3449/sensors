import logging

from sensors.config.constants import *


class Transport:
    TRANSPORT_TYPE_HTTPS = CFG_TRANSPORT_TYPE_HTTPS
    IDENTIFIER_SEPARATOR = '|'

    def __init__(self, typ, **kwargs):
        self.typ = typ
        self.properties = dict(kwargs)

    @classmethod
    def get_instance(cls, typ, **kwargs):
        if typ == Transport.TRANSPORT_TYPE_HTTPS:
            return HttpsTransport(typ, **kwargs)
        else:
            mesg = "Unknown transport {0}".format(typ)
            logging.error(mesg)
            raise ValueError(mesg)

    def identifier(self) -> str:
        raise NotImplementedError


class HttpsTransport(Transport):
    """HTTPS transport with JWT authentication

    """
    def __init__(self, typ, **kwargs):
        # Make sure required elements are present
        get_config_element(CFG_TRANSPORT_HTTPS_AUTH_URL,
                           kwargs, CFG_PROPERTIES)
        get_config_element(CFG_URL,
                           kwargs, CFG_PROPERTIES)
        get_config_element(CFG_TRANSPORT_HTTPS_JWT_ID,
                           kwargs, CFG_PROPERTIES)
        get_config_element(CFG_TRANSPORT_HTTPS_JWT_KEY,
                           kwargs, CFG_PROPERTIES)
        super().__init__(typ, **kwargs)

    def identifier(self) -> str:
        return Transport.IDENTIFIER_SEPARATOR.join((self.typ, self.properties[CFG_URL]))

    def auth_url(self) -> str:
        return self.properties[CFG_TRANSPORT_HTTPS_AUTH_URL]

    def url(self) -> str:
        return self.properties[CFG_URL]

    def jwt_id(self) -> str:
        return self.properties[CFG_TRANSPORT_HTTPS_JWT_ID]

    def jwt_key(self) -> str:
        return self.properties[CFG_TRANSPORT_HTTPS_JWT_KEY]


def get_config_element(element_name, container, container_name):
    if element_name not in container:
        mesg = "{container_name} {container} does not contain element {element_name}".\
            format(container_name=container_name, container=str(container),
                   element_name=element_name)
        logging.error(mesg)
        raise Exception(mesg)
    return container[element_name]
