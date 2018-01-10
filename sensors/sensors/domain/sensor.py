
class Sensor:
    def __init__(self, name, *args):
        self.name = name
        self.observed_properties = list(args)
