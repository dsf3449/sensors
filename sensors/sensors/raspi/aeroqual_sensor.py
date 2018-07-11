#!/usr/bin/python

import math
import time
import os
import sensors.raspi.constants as constants
import RPi.GPIO as GPIO

#Logical GPIO numbering schema
GPIO.setmode(GPIO.BCM)

# set up the SPI interface pins
GPIO.setup(constants.SPI_MOSI, GPIO.OUT)
GPIO.setup(constants.SPI_MISO, GPIO.IN)
GPIO.setup(constants.SPI_CLK, GPIO.OUT)
GPIO.setup(constants.SPI_CS, GPIO.OUT)


class ADCSPI_AEROQUAL_SM50():
    def readadc(self):
        """read SPI data from MCP3002 chip, 2 possible adc's (0 thru 1)"""
        adcnum = 1
        clockpin = constants.SPI_CLK
        mosipin = constants.SPI_MOSI
        misopin = constants.SPI_MISO
        cspin = constants.SPI_CS
        if ((adcnum > 1) or (adcnum < 0)):
            return -1
        GPIO.output(cspin, True)

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)  # bring CS low

        commandout = adcnum << 1
        commandout |= 0x0F  # start bit + single-ended bit + MSBF bit
        commandout <<= 4  # we only need to send 4 bits here

        for i in range(4):
            if (commandout & 0x80):
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

    def voltageADC(self):
        """Calculates voltage from Analog to Digital Converter in medium voltage (mV)"""
        voltage = int(round(((self.adc_average() * constants.VREF * 2) / constants.RESOLUTION_MQ3002), 0)) + constants.CALIBRATION
        return voltage

    def adc_average(self):
        """Analog to Digital Conversion from the MQ3002 chip to get voltage
           Get 5 reading to get a stable value"""
        AnalogToDigitalValueAvg = 0.0
        for i in range(0, constants.READ_SAMPLE_VALUES):
            AnalogToDigitalValueAvg += self.readadc()
            time.sleep(constants.READ_SAMPLE_TIME)  # Every five seconds
            AnalogToDigitalValueAvg = AnalogToDigitalValueAvg / constants.READ_SAMPLE_VALUES
        return AnalogToDigitalValueAvg


    def convertADCToPPB(self):
        """Converts the ADC value to Parts Per Billion (ppb)"""
        ppb = (500.0 / 1024.0) * self.adc_average()
        return ppb

"""
from aeroqual_sensor import ADCSPI_AEROQUAL_SM50

adcspi_aeroqual = ADCSPI_AEROQUAL_SM50()

def main():
    try:
        print ("Aeroqual Sensor Data")
        while True:
            adcspi_aeroqual.readadc()
            adcspi_aeroqual.adc_average()
            adcspi_aeroqual.voltageADC()
            data = adcspi_aeroqual.convertADCToPPB()
            print ("Ozone Concentration : %.3f ppb" % data)
            print (" ********************************* ")
            time.sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup()


if __name__ == "__main__": main()
"""
