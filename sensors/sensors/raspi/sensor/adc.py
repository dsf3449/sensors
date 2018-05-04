from enum import Enum

from sensors.common.constants import CFG_SENSOR_ADC_MCP3002, CFG_SENSOR_ADC_ADS1015

class ADCType(Enum):
    MCP3002 = 1
    ADS1015 = 2

    @classmethod
    def from_string(cls, adc_str):
        if adc_str == CFG_SENSOR_ADC_MCP3002:
            return ADCType.MCP3002
        elif adc_str == CFG_SENSOR_ADC_ADS1015:
            return ADCType.ADS1015
        else:
            raise ValueError("Unknown ADC type: " + adc_str)
