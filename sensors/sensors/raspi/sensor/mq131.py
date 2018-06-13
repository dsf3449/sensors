"""
Driver for MQ131 gas sensor for Raspberry Pi 3 with MCP3002 ADC.
This driver is based on the Arduino driver that can be found here:
    https://github.com/empierre/arduino/blob/master/AirQuality-Multiple_Gas_Sensor1_4.ino
MCP3002-specific code based on:
    https://dmt195.wordpress.com/2012/09/26/mcp3002-example-code-for-raspberry-pi-adc-through-spi/
"""
import math
import time

from sensors.raspi import import_raspi_gpio
GPIO = import_raspi_gpio()

from sensors.raspi import import_adafruit_adc
ADAFRUIT_ADC = import_adafruit_adc()

from sensors.domain.sensor import OzoneSensor
from sensors.common.constants import *
from sensors.raspi.constants import *
from sensors.domain.adc import ADCType


class Mq131(OzoneSensor):
    NAME = CFG_SENSOR_TYPE_MQ131
    PROPERTY_RO = 'Ro'

    # Equation values
    # MQ131 O3 coordinates on curve
    PC_CURVE_0 = 42.84561841
    PC_CURVE_1 = -1.043297135
    RL_MQ131 = 0.679  # MQ131 Sainsmart Resistor Load value
    RO_DEFAULT_MQ131 = 2.501  # Must be calibrated per sensor, this is used as a default
    READ_SAMPLE_TIMES = 5  # Number of samples to read to get average
    READ_SAMPLE_INTERVAL = 0.05
    CALIBRATION_SAMPLE_TIMES = 50
    CALIBRATION_SAMPLE_INTERVAL = 0.5
    ADC_DEFAULT = CFG_SENSOR_ADC_MCP3002
    ADC_ADS1015_CHANNEL = 0
    ADC_ADS1015_GAIN = 1.0

    RO_MULT = math.exp((math.log(PC_CURVE_0 / 10) / PC_CURVE_1))
    RESISTANCE_NUMERATOR = 1024.0 * 1000.0 * RL_MQ131

    def _initialize(self):
        if self.adc_type == ADCType.MCP3002:
            self._initialize_mcp3002()
        elif self.adc_type == ADCType.ADS1015:
            self._initialize_ads1015()

    def _initialize_ads1015(self):
        self.ads1015_adc = ADAFRUIT_ADC.ADS1015()

    def _initialize_mcp3002(self):
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        # set up the SPI interface pins
        GPIO.setup(SPI_MOSI, GPIO.OUT)
        GPIO.setup(SPI_MISO, GPIO.IN)
        GPIO.setup(SPI_CLK, GPIO.OUT)
        GPIO.setup(SPI_CS, GPIO.OUT)

    def _ozone(self):
        self._initialize()

        # Average of 5 readings
        adc_avg = self._adc_average()
        # Voltage for metadata
        voltage = self._voltage_adc(adc_avg)
        # Get the Rs value (O3 concentration) from the average of the 5 readings
        rs = self._mq_resistance(adc_avg)
        # Get the Ro (Clean Air) value from the average of the 5 readings
        ratio = self._rs_over_ro_ratio(rs, self.r_o)
        ppm = self._calculate_ppm_o3(ratio, self.r_o)
        # Metadata
        parameters = {"voltage": str(voltage),
                      "Rs": str(rs),
                      "Ro": str(self.r_o),
                      "Rs_Ro_Ratio": str(ratio)}
        return ppm, parameters

    def _readadc(self):
        if self.adc_type == ADCType.MCP3002:
            return self._readadc_mcp3002()
        elif self.adc_type == ADCType.ADS1015:
            return self._readadc_ads1015()

    def _readadc_mcp3002(self):
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
            if GPIO.input(misopin):
                adcout |= 0x1
        GPIO.output(cspin, True)

        adcout /= 2  # first bit is 'null' so drop it
        return adcout

    def _readadc_ads1015(self):
        return self.ads1015_adc.read_adc(Mq131.ADC_ADS1015_CHANNEL,
                                         gain=Mq131.ADC_ADS1015_GAIN)

    # Calculates voltage from Analog to Digital Converter in medium voltage (mV)
    def _voltage_adc(self, adc_avg):
        if self.adc_type == ADCType.MCP3002:
            self._voltage_mcp3002(adc_avg)
        elif self.adc_type == ADCType.ADS1015:
            self._voltage_ads1015(adc_avg)

    def _voltage_mcp3002(self, adc_avg):
        return int(round(((adc_avg * VREF * 2) / RESOLUTION_MQ3002), 0)) + CALIBRATION

    def _voltage_ads1015(self, adc_avg):
        return int(round(((adc_avg * VREF * 2) / RESOLUTION_ADS1015), 0)) + CALIBRATION

    def _adc_average(self):
        # Analog to Digital Conversion from the MQ3002 chip to get voltage
        # Get 5 reading to get a stable value
        adc_avg = 0.0
        for i in range(0, Mq131.READ_SAMPLE_TIMES):
            adc_avg += self._readadc()
            time.sleep(Mq131.READ_SAMPLE_INTERVAL)  # Every five seconds
            adc_avg = adc_avg / Mq131.READ_SAMPLE_TIMES
        return adc_avg

    def _mq_resistance(self, adc):
        """Calculates the sensor resistance (Rs)"""
        return self.RESISTANCE_NUMERATOR / (adc - Mq131.RL_MQ131)

    def _measure_Ro(self, rl=RL_MQ131):
        """Calculates the sensor resistance of clean air from the MQ131 sensor"""
        self._initialize()

        val = 0.0
        for i in range(Mq131.CALIBRATION_SAMPLE_TIMES):
            val += self._mq_resistance(self._readadc())
            time.sleep(Mq131.CALIBRATION_SAMPLE_INTERVAL)
        val = val / Mq131.CALIBRATION_SAMPLE_TIMES
        # Divide final result by 1000 to be consistent with Ro value scale used
        # reference Arduino driver
        return val * Mq131.RO_MULT / 1000.0

    def _rs_over_ro_ratio(self, rs, ro):
        """Calculates the ratio of Rs and Ro from a sensor"""
        return rs / ro

    def _calculate_ppb_o3(self, ratio, ro):
        """Calculate the final concentration value"""
        return self._calculate_ppm_o3(ratio, ro) * 1000.0

    def _calculate_ppm_o3(self, ratio, ro):
        """Calculate the final concentration value"""
        return (Mq131.PC_CURVE_0 * math.pow((ratio / ro), Mq131.PC_CURVE_1))

    def __init__(self, typ, *args, **kwargs):
        super().__init__(typ, *args, **kwargs)
        self.r_o = float(self.properties.get(Mq131.PROPERTY_RO, Mq131.RO_DEFAULT_MQ131))
        self.adc_type = ADCType.from_string(self.properties.get(CFG_PROPERTY_ADC, Mq131.ADC_DEFAULT))
