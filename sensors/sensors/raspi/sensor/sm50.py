"""
Driver for Aeroqual SM50 ozone gas sensor with ADS1015 ADC.
Sensor datasheet can be found here:
    https://www.aeroqual.com/wp-content/uploads/2010/12/AQL-SM50-OEM-Sensor-Module-Specs.pdf
"""
import time

from sensors.raspi import import_adafruit_adc
ADAFRUIT_ADC = import_adafruit_adc()

from sensors.domain.sensor import OzoneSensor
from sensors.common.constants import *


class Sm50(OzoneSensor):
    NAME = CFG_SENSOR_TYPE_SM50

    READ_SAMPLE_TIMES = 5  # Number of samples to read to get average
    READ_SAMPLE_INTERVAL = 0.05
    ADC_ADS1015_CHANNEL = 2
    ADC_ADS1015_GAIN = 1
    SM50_DN_MAX = 255
    SM50_MAX_PPM = 0.5

    def _initialize(self):
        self.ads1015_adc = ADAFRUIT_ADC.ADS1015()

    def _ozone(self):
        self._initialize()

        # Average of 5 readings
        adc_avg = self._adc_average()
        ppm = self._calculate_ppm_o3(adc_avg)
        # Metadata
        parameters = {"adc_avg": str(adc_avg)}
        return ppm, parameters

    def _readadc(self):
        return self.ads1015_adc.read_adc(Sm50.ADC_ADS1015_CHANNEL,
                                         gain=Sm50.ADC_ADS1015_GAIN)

    def _adc_average(self):
        # Get 5 readings from the ADC to get a stable value
        adc_avg = 0.0
        for i in range(0, Sm50.READ_SAMPLE_TIMES):
            adc_avg += self._readadc()
            time.sleep(Sm50.READ_SAMPLE_INTERVAL)  # Every five seconds
        adc_avg = adc_avg / Sm50.READ_SAMPLE_TIMES
        return adc_avg

    @staticmethod
    def _calculate_ppm_o3(adc):
        """Calculate the final concentration value"""
        assert adc <= Sm50.SM50_DN_MAX
        return (adc / Sm50.SM50_DN_MAX) * Sm50.SM50_MAX_PPM

    def __init__(self, typ, *args, **kwargs):
        super().__init__(typ, *args, **kwargs)
