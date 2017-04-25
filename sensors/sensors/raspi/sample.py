#!/usr/bin/env python3

import multiprocessing as mp
import datetime
import math
import time
import sched
import os
import sys
import sensors.persistence.spool as spool
from sensors.common.logging import configure_logger
from sensors.domain.observation import Observation
import sensors.common.constants as CONSTANTS
import RPi.GPIO as GPIO

# Logical GPIO numbering schema
GPIO.setmode(GPIO.BCM)

# set up the SPI interface pins
GPIO.setup(CONSTANTS.SPIMOSI, GPIO.OUT)
GPIO.setup(CONSTANTS.SPIMISO, GPIO.IN)
GPIO.setup(CONSTANTS.SPICLK, GPIO.OUT)
GPIO.setup(CONSTANTS.SPICS, GPIO.OUT)

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


# read SPI data from MCP3002 chip, 2 possible adc's (0 thru 1)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
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


# Calculates voltage from Analog to Digital Converter in medium voltage (mV)
def voltageADC(readadc):
    voltage = int(round(((readadc * CONSTANTS.vref * 2) / CONSTANTS.resolution), 0)) + CONSTANTS.calibration
    return voltage


# Calculates vrl for resistance of sensor equation
# def vrl(adc):
#    vrl = adc * 5 / 4096.0
#    return vrl

# Calculates the sensor resistance (Rs)
def MQResistance(readadc, rl_value):
    return (1024 * 1000 * rl_value) / (readadc - rl_value)
    # Rs = (22000 * (5 - vrl)) / vrl
    # return Rs


# Calculates the sensor resistance of clean air from the MQ131 sensor
def MQCalibration(rs):
    Ro = rs * math.exp((math.log(CONSTANTS.pcCurve[0] / 0.010) / CONSTANTS.pcCurve[1]))
    return Ro


# Calculates the ratio of Rs and Ro from a sensor
def RsRoRatio(Rs, Ro):
    return (Rs / Ro)


# Calculates the Parts Per Million (ppm) value
def calculatePPM(RsRoRatio, Ro):
    ppm = (CONSTANTS.pcCurve[0] * math.pow((RsRoRatio / Ro), CONSTANTS.pcCurve[1]))
    return ppm


# Converts the Parts Per Million (ppm) value to Parts Per Billion (ppb)
def convertPPMToPPB(ppm):
    return ppm * 1000


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
    adc_num = 0  # Reads from channel 0
    count = 0
    foi_id = os.environ["CGIST_FOI_ID"]
    ds_id = os.environ["CGIST_DS_ID_MQ131"]

    # Analog to Digital Conversion from the MQ3002 chip to get voltage
    # Get 5 reading to get a stable value
    o3SensorAnalogValue1 = readadc(adc_num, CONSTANTS.SPICLK, CONSTANTS.SPIMOSI, CONSTANTS.SPIMISO,
                                   CONSTANTS.SPICS)
    # print "The Analog to Digital value1 ",
    # print  o3SensorAnalogValue1, "\t",
    count += 1
    time.sleep(5)  # Every five seconds
    o3SensorAnalogValue2 = readadc(adc_num, CONSTANTS.SPICLK, CONSTANTS.SPIMOSI, CONSTANTS.SPIMISO,
                                   CONSTANTS.SPICS)
    # print "The Analog to Digital value2 ",
    # print  o3SensorAnalogValue2, "\t",
    count += 1
    time.sleep(5)  # Every five seconds
    o3SensorAnalogValue3 = readadc(adc_num, CONSTANTS.SPICLK, CONSTANTS.SPIMOSI, CONSTANTS.SPIMISO,
                                   CONSTANTS.SPICS)
    # print "The Analog to Digital value3 ",
    # print  o3SensorAnalogValue3, "\t",
    count += 1
    time.sleep(5)  # Every five seconds
    o3SensorAnalogValue4 = readadc(adc_num, CONSTANTS.SPICLK, CONSTANTS.SPIMOSI, CONSTANTS.SPIMISO,
                                   CONSTANTS.SPICS)
    # print "The Analog to Digital value4 ",
    # print  o3SensorAnalogValue4, "\t",
    count += 1
    time.sleep(5)  # Every five seconds
    o3SensorAnalogValue5 = readadc(adc_num, CONSTANTS.SPICLK, CONSTANTS.SPIMOSI, CONSTANTS.SPIMISO,
                                   CONSTANTS.SPICS)
    # print "The Analog to Digital value5 ",
    # print  o3SensorAnalogValue5, "\t",
    count += 1

    # Average reading
    o3SensorAnalogValueAvg = (o3SensorAnalogValue1 + o3SensorAnalogValue2 + o3SensorAnalogValue3 + o3SensorAnalogValue4
                              + o3SensorAnalogValue5) / count
    logger.debug("The Analog to Digital value avg ", )
    logger.debug(o3SensorAnalogValueAvg, "\t")
    count = 0  # reset counter

    # Voltage from average reading
    voltage = voltageADC(o3SensorAnalogValueAvg)

    # Get the Rs value (O3 concentrations of gases) from the average of the 5 readings
    Rs = MQResistance(o3SensorAnalogValueAvg, CONSTANTS.RL_MQ131)

    # Get the Ro (Clean Air) value from the average of the 5 readings
    Ro = MQCalibration(Rs)

    # Get Ratio from the Rs and Ro values
    Rs_Ro_Ratio = RsRoRatio(Rs, Ro)

    # Get the ppm value from the average of the 5 readings
    ppm = calculatePPM(Rs_Ro_Ratio, Ro)

    # Convert the ppm value to ppb value
    ppb = convertPPMToPPB(ppm)

    logger.debug("The PPB ", )
    logger.debug(ppb, "\t")

    parameters = {"voltage": str(voltage),
                  "Rs": str(Rs),
                  "Ro": str(Ro),
                  "Rs_Ro_Ratio": str(Rs_Ro_Ratio)}

    return generate_observation(foi_id, ds_id,
                                datetime.datetime.now().isoformat(),
                                str(ppb), parameters)


def generate_observations_minute(queue):
    logger.debug("Generating O3 observation...")
    o = generate_ozone_MQ131()
    logger.debug("Queuing observation {0}...".format(str(o)))
    queue.put(o)


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
            s.enter(CONSTANTS.SAMPLE_INTERVAL_ONE_MINUTE,
                    CONSTANTS.SCHEDULE_PRIORITY_DEFAULT,
                    generate_observations_minute,
                    argument=(q,))
            # Run scheduled events
            logger.debug("Sampler: Running scheduler...")
            s.run()
            logger.debug("Sampler: End of iteration.")

    except KeyboardInterrupt:
        GPIO.cleanup()
    finally:
        if p:
            p.join()
        logger.info("Raspberry Pi sensor: exiting.")
