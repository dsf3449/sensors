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

    def _read_results(self):
        pm1 = None
        pm25 = None
        pm10 = None
        try:
            cp = subprocess.run(["sample_opcn2"], stdout=subprocess.PIPE, universal_newlines=True)
            pm = json.loads(cp.stdout.split('\n')[:-1][0])
            pm1 = pm['PM1']
            pm25 = pm['PM2.5']
            pm10 = pm['PM10']
        except:
            pm1 = pm25 = pm10 = math.nan

        results = {CFG_OBSERVED_PROPERTY_PM1: pm1,
                   CFG_OBSERVED_PROPERTY_PM25: pm25,
                   CFG_OBSERVED_PROPERTY_PM10: pm10}
        parameters = {}
        return results, parameters

    def __init__(self, typ, *args, **kwargs):
        super().__init__(typ, *args, **kwargs)
