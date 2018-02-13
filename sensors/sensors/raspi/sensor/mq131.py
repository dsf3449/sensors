import math
import time

import RPi.GPIO as GPIO

from sensors.domain.sensor import OzoneSensor
from sensors.config.constants import *
from sensors.raspi.constants import *


class Mq131(OzoneSensor):
    NAME = CFG_SENSOR_TYPE_MQ131
    RO_MULT = math.exp((math.log(PC_CURVE_0 / 0.010) / PC_CURVE_1))
    RESISTANCE_NUMERATOR = 1024.0 * 1000.0 * RL_MQ131

    def _ozone(self):
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        # set up the SPI interface pins
        GPIO.setup(SPI_MOSI, GPIO.OUT)
        GPIO.setup(SPI_MISO, GPIO.IN)
        GPIO.setup(SPI_CLK, GPIO.OUT)
        GPIO.setup(SPI_CS, GPIO.OUT)

        # Average of 5 readings
        adc_avg = self._adc_average()
        # Voltage for metadata
        voltage = self._voltage_adc(adc_avg)
        # Get the Rs value (O3 concentration) from the average of the 5 readings
        rs = self._mq_resistance(adc_avg)
        # Get the Ro (Clean Air) value from the average of the 5 readings
        # ro = self._measure_Ro(rs)
        ro = RO_DEFAULT_MQ131
        ratio = self._rs_over_ro_ratio(rs, ro)
        ppb = self._calculate_ppb_o3(ratio, ro)
        # Metadata
        parameters = {"voltage": str(voltage),
                      "Rs": str(rs),
                      "Ro": str(ro),
                      "Rs_Ro_Ratio": str(ratio)}
        return ppb, parameters

    def _readadc(self):
        adcnum = 0
        clockpin = SPI_CLK
        mosipin = SPI_MOSI
        misopin = SPI_MISO
        cspin = SPI_CS
        if (adcnum > 1) or (adcnum < 0):
            return -1
        GPIO.output(cspin, True)

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)  # bring CS low

        commandout = adcnum << 1
        commandout |= 0x0D  # start bit + single-ended bit + MSBF bit
        commandout <<= 4  # we only need to send 4 bits here

        for i in range(4):
            if commandout & 0x80:
                GPIO.output(mosipin, True)
            else:
                GPIO.output(mosipin, False)
            commandout <<= 1
            GPIO.output(clockpin, True)
            GPIO.output(clockpin, False)

        adcout = 0

        # read in one null bit and 10 ADC bits
        for i in range(11):
            GPIO.output(clockpin, True)
            GPIO.output(clockpin, False)
            adcout <<= 1
            if (GPIO.input(misopin)):
                adcout |= 0x1
        GPIO.output(cspin, True)

        adcout /= 2  # first bit is 'null' so drop it
        return adcout

    # Calculates voltage from Analog to Digital Converter in medium voltage (mV)
    def _voltage_adc(self, adc_avg):
        voltage = int(round(((adc_avg * VREF * 2) / RESOLUTION), 0)) + CALIBRATION
        return voltage

    def _adc_average(self):
        # Analog to Digital Conversion from the MQ3002 chip to get voltage
        # Get 5 reading to get a stable value
        adc_avg = 0.0
        for i in range(0, READ_SAMPLE_VALUES):
            adc_avg += self._readadc()
            time.sleep(READ_SAMPLE_TIME)  # Every five seconds
            adc_avg = adc_avg / READ_SAMPLE_VALUES
        return adc_avg

    def _mq_resistance(self, adc_avg):
        """Calculates the sensor resistance (Rs)"""
        return self.RESISTANCE_NUMERATOR / (adc_avg - RL_MQ131)

    def _measure_Ro(self, rs):
        """Calculates the sensor resistance of clean air from the MQ131 sensor"""
        Ro = rs * self.RO_MULT
        return Ro

    def _rs_over_ro_ratio(self, rs, ro):
        """Calculates the ratio of Rs and Ro from a sensor"""
        return rs / ro

    def _calculate_ppb_o3(self, ratio, ro):
        """Calculate the final concentration value"""
        ppm = (PC_CURVE_0 * math.pow((ratio / ro), PC_CURVE_1))
        ppb = ppm * 1000.0
        return ppb

    def __init__(self, typ, *args):
        super().__init__(typ, *args)
