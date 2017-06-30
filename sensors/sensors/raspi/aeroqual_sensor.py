#!/usr/bin/python

import math
import time
import os
import RPi.GPIO as GPIO

#Logical GPIO numbering schema
GPIO.setmode(GPIO.BCM)

# change these as desired
SPI_CLK = 11  # Serial Peripheral Interface Clock
SPI_MOSI = 10  # Serial Peripheral Interface data out from MCP3002 chip
SPI_MISO = 9  # Serial Peripheral Interface data in from MCP3002 chip
SPI_CS = 8  # Serial Peripheral Interface chip select

# set up the SPI interface pins
GPIO.setup(SPI_MOSI, GPIO.OUT)
GPIO.setup(SPI_MISO, GPIO.IN)
GPIO.setup(SPI_CLK, GPIO.OUT)
GPIO.setup(SPI_CS, GPIO.OUT)

Aeroqual_Sample_Time = 5

# Sets up pin
'''def setuppins(*spipins):
    GPIO.setmode(GPIO.BCM)
    for spi in spipins:
        if (spi == SPI_MOSI):
            GPIO.setup(spi, GPIO.IN)
        else:
            GPIO.setup(spi, GPIO.OUT)'''


# read SPI data from MCP3002 chip, 2 possible adc's (0 thru 1)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
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

def adc_average(adc_num):
    # Analog to Digital Conversion from the MQ3002 chip to get voltage
    # Get 5 reading to get a stable value
    aeroqualSensorAnalogValueAvg = 0.0
    for i in range(0, Aeroqual_Sample_Time):
        aeroqualSensorAnalogValueAvg += readadc(adc_num, SPI_CLK, SPI_MOSI, SPI_MISO, SPI_CS)
        time.sleep(0.1)  # Every five seconds
    aeroqualSensorAnalogValueAvg = aeroqualSensorAnalogValueAvg / Aeroqual_Sample_Time
    return aeroqualSensorAnalogValueAvg


# Converts the ADC value to Parts Per Billion (ppb)
def convertADCToPPB(adc):
    return (500.0 / 1024.0) * adc


def main():
    try:
        adc_num = 1  # Reads from channel 0
        print ("Aeroqual Sensor Data")
        while True:
            adc_avg = adc_average(adc_num)
            ppb = convertADCToPPB(adc_avg)

            print ("The Analog to Digital value avg: " + str(adc_avg))
            print ("PPB: " + str(ppb))
    except KeyboardInterrupt:
        GPIO.cleanup()


if __name__ == "__main__": main()
