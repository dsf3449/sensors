import subprocess
import json
import math

from sensors.domain.sensor import ParticulateMatterSensor
from sensors.common.constants import *


class OPCN2(ParticulateMatterSensor):
    NAME = CFG_SENSOR_TYPE_OPCN2

    SPI_BUS = 0
    SPI_DEVICE = 0
    SPI_MODE = 1
    SPI_SPEED_HZ = 500000

    def _particulates(self):
        result = None
        parameters = None
        try:
            cp = subprocess.run(["sample_opcn2"], stdout=subprocess.PIPE, universal_newlines=True)
            pm = json.loads(cp.stdout.split('\n')[:-1][0])
            result = float(pm['PM2.5'])
            parameters = {"pm1": str(pm['PM1']),
                          "pm10": str(pm['PM10'])}
        except:
            result = math.nan
            parameters = {"pm1": str(math.nan),
                          "pm10": str(math.nan)}

        return result, parameters

    def __init__(self, typ, *args, **kwargs):
        super().__init__(typ, *args, **kwargs)
