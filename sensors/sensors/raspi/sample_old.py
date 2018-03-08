###  CGI Digital Services - LEaRN
###  March 2017
###  Application to read O3 Senser (MQ131) from the Raspberry Pi 3 Rev. B
###  Converts the analog value to digital value with the MCP3002 chip
###  Once we have that value, it will convert it to an equation to get the parts per billion (ppb) value
###  Finally, the values are stored in spooler in sqlite database in memory.
###  V0.0.2

import multiprocessing as mp
import datetime
import math
import time
import sched
import os
import sys
import sensors.persistence.spool as spool
from sensors.common.logging import configure_logger
from sensors.raspi.mq131_ozone_current import ADCSPI_MQ131_CURRENT as ADCSPI_MQ131
from sensors.raspi.aeroqual_sensor import ADCSPI_AEROQUAL_SM50
import sensors.raspi.dht11 as dht11
from sensors.raspi.pm_sample import readlineCR
import sensors.raspi.opc as opc
from sensors.domain.observation import Observation
import sensors.raspi.constants as constants
import serial
import spidev
import RPi.GPIO as GPIO

"""MQ131 and aeroqual sensor initialization"""

# Logical GPIO numbering schema
GPIO.setmode(GPIO.BCM)

# set up the SPI interface pins
GPIO.setup(constants.SPI_MOSI, GPIO.OUT)
GPIO.setup(constants.SPI_MISO, GPIO.IN)
GPIO.setup(constants.SPI_CLK, GPIO.OUT)
GPIO.setup(constants.SPI_CS, GPIO.OUT)

"""End of MQ131 and aeroqual sensor initialization"""

"""DFRobot PM sensor initializtion"""

port = serial.Serial("/dev/serial0", baudrate=9600, timeout=2)

"""End of DFRobot PM sensor initializtion"""

"""Alphasense OPC-N2 PM sensor initialization"""

# Open a SPI connection on CE0
spi = spidev.SpiDev()
spi.open(0, 0)

# Set the SPI mode and clock speed
spi.mode = 1
spi.max_speed_hz = 500000

alpha = opc.OPCN2(spi)

"""End of Alphasense OPC-N2 PM sensor initialization"""

MQ_Sample_Time = 5

# Configure logging
logger = configure_logger()

CGIST_FOI_ID = None
CGIST_DS_ID_MQ131 = None
try:
    CGIST_FOI_ID = os.environ["CGIST_FOI_ID"]
    CGIST_DS_ID_MQ131 = os.environ["CGIST_DS_ID_MQ131"]
except KeyError:
    mesg = "Environment variable CGIST_FOI_ID or CGIST_DS_ID_MQ131 not defined."
    logger.error(mesg)
    sys.exit(mesg)


def generate_observation(featureOfInterestId, datastreamId, phenomenonTime,
                         result, parameters):
    o = Observation()
    o.featureOfInterestId = featureOfInterestId
    o.datastreamId = datastreamId
    o.phenomenonTime = phenomenonTime
    o.result = result
    o.set_parameters(**parameters)

    return o


def generate_ozone_MQ131():
    foi_id = os.environ["CGIST_FOI_ID"]
    ds_id = os.environ["CGIST_DS_ID_MQ131"]
    adcspi_mq131 = ADCSPI_MQ131()

    adcspi_mq131.readadc()
    o3SensorAnalogValueAvg = adcspi_mq131.adc_average()

    logger.debug("The Analog to Digital value avg: " + str(o3SensorAnalogValueAvg))

    # Voltage from average reading
    voltage = adcspi_mq131.voltageADC()

    adcspi_mq131.MQResistance()

    # Get the Rs value (O3 concentrations of gases) from the average of the 5 readings
    Rs = adcspi_mq131.measure_Rs()

    # Get the Ro (Clean Air) value from the average of the 5 readings
    Ro = adcspi_mq131.measure_Ro()

    # Get Ratio from the Rs and Ro values
    Rs_Ro_Ratio = adcspi_mq131.measure_ratio()

    # Get the ppm value from the average of the 5 readings
    adcspi_mq131.calculate_ppm_O3()

    # Convert the ppm value to ppb value
    ppb = adcspi_mq131.convertPPMToPPB()

    logger.debug("The PPB: " + str(ppb['o3']))

    parameters = {"voltage": str(voltage),
                  "Rs": str(Rs),
                  "Ro": str(Ro),
                  "Rs_Ro_Ratio": str(Rs_Ro_Ratio)}

    return generate_observation(foi_id, ds_id,
                                datetime.datetime.now().isoformat(),
                                str(ppb), parameters)


def generate_ozone_aeroqual():
    foi_id = os.environ["CGIST_FOI_ID"]
    ds_id = os.environ["CGIST_DS_ID_MQ131"] # Will be different datastream
    adcspi_aeroqual = ADCSPI_AEROQUAL_SM50()

    adcspi_aeroqual.readadc()
    aeroqualSensorAnalogValueAvg = adcspi_aeroqual.readadc()

    logger.debug("The Analog to Digital value avg: " + str(aeroqualSensorAnalogValueAvg))

    voltage = adcspi_aeroqual.voltageADC()

    ppb = adcspi_aeroqual.convertADCToPPB()

    logger.debug("The PPB: " + str(ppb['aeroqual']))

    parameters = {"voltage": str(voltage)}

    return generate_observation(foi_id, ds_id,
                                datetime.datetime.now().isoformat(),
                                str(ppb), parameters)

def generate_temp_humdity():
    foi_id = os.environ["CGIST_FOI_ID"]
    ds_id = os.environ["CGIST_DS_ID_MQ131"]  # Will be different datastream

    # read data using pin 14
    instance = dht11.DHT11(pin=17)
    result = instance.read()

    if result.is_valid():
        parameters = {"Temperature C": str(result.temperature),
                      "Temperature F": str(result.temperature * 1.8 + 32),
                      "Humidity": str(result.humidity)}

        logger.debug("Last valid input: " + str(datetime.datetime.now()))
        logger.debug("Temperature: %d C" % result.temperature)
        logger.debug("Temperature: %d F" % result.temperature * 1.8 + 32)
        logger.debug("Humidity: %d %%" % result.humidity)

        return generate_observation(foi_id, ds_id,
                                    datetime.datetime.now().isoformat(),
                                    parameters)
    else:
        logger.debug("Error: %d" % result.error_code)


def generate_pm_dfrobot():
    foi_id = os.environ["CGIST_FOI_ID"]
    ds_id = os.environ["CGIST_DS_ID_MQ131"]  # Will be different datastream

    pm_info = readlineCR(port)
    parameters = {};

    if pm_info.valid:
        logger.debug(pm_info.pm10, pm_info.pm25, pm_info.pm100)
        parameters = {"pm1.0": pm_info.pm10,
                      "pm2.5": pm_info.pm25,
                      "pm10.0": pm_info.pm100}
    else:
        logger.debug("PM data not available at this time.")

    return generate_observation(foi_id, ds_id,
                                    datetime.datetime.now().isoformat(),
                                    parameters)

def generate_pm_opcn2():
    foi_id = os.environ["CGIST_FOI_ID"]
    ds_id = os.environ["CGIST_DS_ID_MQ131"]  # Will be different datastream

    # Turn on the OPC
    alpha.on()
    # Read the PM data
    print ("OPC PM Data")
    logger.debug("OPC PM Data")
    for key, value in alpha.pm().items():
        logger.debug("Key: {}\tValue: {}".format(key, value))

    # Returns dictionary of PM values
    return generate_observation(foi_id, ds_id,
                                    datetime.datetime.now().isoformat(),
                                    alpha.pm())


def generate_observations_minute(queue):
    logger.debug("Generating O3 observation...")
    o_one = generate_ozone_MQ131()
    logger.debug("Queuing observation {0}...".format(str(o_one)))
    queue.put(o_one)
    #logger.debug("Generating aeroqual ozone observation...")
    #o_two = generate_ozone_aeroqual()
    #logger.debug("Queing observation {0}...".format(str(o_two)))
    #queue.put(o_two)


def main():
    p = None

    try:
        # Start process to send data to
        mp.set_start_method('spawn')
        q = mp.Queue()
        p = mp.Process(target=spool.spool_data, args=(q,))
        p.start()

        s = sched.scheduler(time.time, time.sleep)

        while True:
            logger.debug("|", )

            # Schedule event to run every minute
            logger.debug("Sampler: scheduling observation sampling...")
            s.enter(constants.SAMPLE_INTERVAL_ONE_MINUTE,
                    constants.SCHEDULE_PRIORITY_DEFAULT,
                    generate_observations_minute,
                    argument=(q,))
            # Run scheduled events
            logger.debug("Sampler: Running scheduler...")
            s.run()
            logger.debug("Sampler: End of iteration.")

    except KeyboardInterrupt:
        GPIO.cleanup()
        # Turn the opc OFF
        alpha.off()
    finally:
        if p:
            p.join()
        logger.info("Raspberry Pi sensor: exiting.")
