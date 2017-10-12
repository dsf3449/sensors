import time

from mq131_ozone_current import ADCSPI_MQ131_CURRENT
from mq131_ozone_future import ADCSPI_MQ131
import constants as constants
import RPi.GPIO as GPIO

# Logical GPIO numbering schema
GPIO.setmode(GPIO.BCM)

# set up the SPI interface pins
GPIO.setup(constants.SPI_MOSI, GPIO.OUT)
GPIO.setup(constants.SPI_MISO, GPIO.IN)
GPIO.setup(constants.SPI_CLK, GPIO.OUT)
GPIO.setup(constants.SPI_CS, GPIO.OUT)

adcspi_mq131_current = ADCSPI_MQ131_CURRENT()
adcspi_mq131_future = ADCSPI_MQ131()


def main():
    try:
        while True:
            adcspi_mq131_current.readadc()
            adcspi_mq131_current.adc_average()
            adcspi_mq131_current.voltageADC()
            adcspi_mq131_current.MQResistance()
            adcspi_mq131_current.measure_Ro()
            adcspi_mq131_current.measure_ratio()
            adcspi_mq131_current.calculate_ppm_O3()
            data_current_alg = adcspi_mq131_current.convertPPMToPPB()
            adcspi_mq131_future.readadc()
            adcspi_mq131_future.adc_average()
            adcspi_mq131_future.voltageADC()
            adcspi_mq131_future.MQResistance()
            adcspi_mq131_future.measure_Rs()
            adcspi_mq131_future.measure_Ro()
            adcspi_mq131_future.measure_ratio()
            adcspi_mq131_future.calculate_ppm_O3()
            data_new_alg = adcspi_mq131_future.convertPPMToPPB()
            print "Ozone Concentration_Current_Algorithm : %.3f ppb" % (data_current_alg['o3'])
            print "Ozone Concentration_New_Algorithm : %.3f ppb" % (data_new_alg['o3'])
            print " ********************************* "
            time.sleep(5)
    except KeyboardInterrupt:
        GPIO.cleanup()


if __name__ == "__main__": main()
