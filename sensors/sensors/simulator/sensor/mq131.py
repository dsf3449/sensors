import random

from sensors.domain.sensor import OzoneSensor
from sensors.common.constants import *
from sensors.domain.adc import ADCType


class Mq131(OzoneSensor):
    NAME = CFG_SENSOR_TYPE_MQ131
    PROPERTY_RO = 'Ro'

    RO_DEFAULT_MQ131 = 2.501
    ADC_DEFAULT = CFG_SENSOR_ADC_MCP3002

    def _ozone(self):
        result = random.uniform(0.001, 0.5)
        r_s = random.uniform(1.23, 54321.12)
        parameters = {"Rs": str(r_s),
                      "Ro": str(self.r_o),
                      "Rs_Ro_Ratio": str(r_s / self.r_o),
                      "adc_avg": str(random(0, 1023))}
        return result, parameters

    def __init__(self, typ, *args, **kwargs):
        super().__init__(typ, *args, **kwargs)
        self.r_o = float(self.properties.get(Mq131.PROPERTY_RO, Mq131.RO_DEFAULT_MQ131))
        self.adc_type = ADCType.from_string(self.properties.get(CFG_PROPERTY_ADC, Mq131.ADC_DEFAULT))
