from sensors.config.constants import *


class Transport:
    TRANSPORT_TYPE_HTTPS = CFG_TRANSPORT_TYPE_HTTPS
    IDENTIFIER_SEPARATOR = '|'

    def __init__(self, typ, **kwargs):
        self.typ = typ
        self.properties = dict(kwargs)

    def identifier(self) -> str:
        raise NotImplementedError

    def transmit(self, repo):
        raise NotImplementedError

    def transmit_interval_seconds(self) -> int:
        return int(self.properties.get(CFG_TRANSPORT_HTTPS_TRANSMIT_INTERVAL_SEC,
                                       self.DEFAULT_TRANSMIT_INTERVAL_SECONDS))
