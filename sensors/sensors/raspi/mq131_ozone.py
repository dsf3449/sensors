#!/usr/bin/python

import time
import math
import sensors.raspi.constants as constants
import RPi.GPIO as GPIO

# Logical GPIO numbering schema
GPIO.setmode(GPIO.BCM)

# set up the SPI interface pins
GPIO.setup(constants.SPI_MOSI, GPIO.OUT)
GPIO.setup(constants.SPI_MISO, GPIO.IN)
GPIO.setup(constants.SPI_CLK, GPIO.OUT)
GPIO.setup(constants.SPI_CS, GPIO.OUT)

MQ_Sample_Time = 5

class ADCSPI_MQ131():
    # read SPI data from MCP3002 chip, 2 possible adc's (0 thru 1)
    def readadc(self):
        adcnum = 0
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
        commandout |= 0x0D  # start bit + single-ended bit + MSBF bit
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


    def MQResistance(self):
        """Calculates the sensor resistance"""
        o3SensorAnalogValueAvg = 0.0
        # Analog to Digital Conversion from the MQ3002 chip to get voltage
        # Get 5 reading to get a stable value
        for i in range(0, MQ_Sample_Time):
            o3SensorAnalogValueAvg += self.readadc()
            time.sleep(5)  # Every five seconds
        o3SensorAnalogValueAvg = o3SensorAnalogValueAvg / MQ_Sample_Time
        self.rsAir = (1024 * 1000 * constants.RL_MQ131) / (o3SensorAnalogValueAvg - constants.RL_MQ131)

    def measure_Ro(self):
        """Calculates the sensor resistance of clean air from the MQ131 sensor"""
        val = 0.0
        for i in range(0, MQ_Sample_Time):
            val += self.rsAir
            time.sleep(0.5)
        Measure_Ro = val / MQ_Sample_Time
        Ro = Measure_Ro * math.exp((math.log(constants.PC_CURVE[0] / 0.010) / constants.PC_CURVE[1]))
        return Ro

    def measure_Rs(self):
        Measure_Rs = 0.0
        for i in range(0, MQ_Sample_Time):
            Measure_Rs += self.rsAir
            time.sleep(0.1)
        Measure_Rs = Measure_Rs / MQ_Sample_Time
        return Measure_Rs

    def measure_ratio(self):
        self.ratio = self.measure_Rs() / self.measure_Ro()
        # print "Ratio = %.3f " % self.ratio

    def calculate_ppm_O3(self):
        """Calculate the final concentration value"""
        ppm = (constants.PC_CURVE[0] * math.pow((self.ratio / self.measure_Ro()), constants.PC_CURVE[1]))
        return ppm

    # Converts the Parts Per Million (ppm) value to Parts Per Billion (ppb)
    def convertPPMToPPB(self):
        ppb = self.calculate_ppm_O3() * 1000
        return {'o3' : ppb}


from mq131_ozone import ADCSPI_MQ131

adcspi_mq131 = ADCSPI_MQ131()

while True:
    adcspi_mq131.readadc()
    adcspi_mq131.MQResistance()
    adcspi_mq131.measure_Rs()
    adcspi_mq131.measure_Ro()
    adcspi_mq131.measure_ratio()
    adcspi_mq131.calculate_ppm_O3()
    data = adcspi_mq131.convertPPMToPPB()
    print "Ozone Concentration : %.3f ppb" % (data['o3'])
    print " ********************************* "
    time.sleep(1)

