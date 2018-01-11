from .observed_property import ObservedProperty


class Sensor:
    def __init__(self, typ, *args):
        self.typ = typ
        self.observed_properties = list(args)
