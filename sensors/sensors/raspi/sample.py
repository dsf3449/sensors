
import multiprocessing as mp
import datetime
import time
import sched
import os
import sensors.persistence.spool as spool
from sensors.common.logging import configure_logger
from sensors.domain.observation import Observation
import sensors.sensors.common.constants as CONSTANTS
import RPi.GPIO as GPIO
import sensors.sensor as MQ131

# Configure logging
logger = configure_logger()

def generate_observation(featureOfInterestId, datastreamId, phenomenonTime,
                         result, parameters):
    o = Observation()
    o.featureOfInterestId = featureOfInterestId
    o.datastreamId = datastreamId
    o.phenomenonTime = phenomenonTime
    o.result = result
    o.set_parameters(**parameters)

    return o


def generate_ozone_MQ131(voltage, Rs, Ro, Rs_Ro_Ratio, ppb):
    foi_id = os.environ.get("CGIST_FOI_ID", "c81a4920-100b-11e7-987b-9b2f50364984")
    ds_id = os.environ.get("CGIST_DS_ID_MQ131", "1e34fad0-100c-11e7-987b-9b2f50364984")
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
            print("|", end=' ')
            for adcnum in range(1):
                # Analog to Digital Conversion from the MQ3002 chip to get voltage
                # Get 5 reading to get a stable value
                o3SensorAnalogValue1 = MQ131.readadc(adcnum, CONSTANTS.SPICLK, CONSTANTS.SPIMOSI, CONSTANTS.SPIMISO, CONSTANTS.SPICS)
                # print "The Analog to Digital value1 ",
                # print  o3SensorAnalogValue1, "\t",
                count += 1
                time.sleep(5)  # Every five seconds
                o3SensorAnalogValue2 = MQ131.readadc(adcnum, CONSTANTS.SPICLK, CONSTANTS.SPIMOSI, CONSTANTS.SPIMISO, CONSTANTS.SPICS)
                # print "The Analog to Digital value2 ",
                # print  o3SensorAnalogValue2, "\t",
                count += 1
                time.sleep(5)  # Every five seconds
                o3SensorAnalogValue3 = MQ131.readadc(adcnum, CONSTANTS.SPICLK, CONSTANTS.SPIMOSI, CONSTANTS.SPIMISO, CONSTANTS.SPICS)
                # print "The Analog to Digital value3 ",
                # print  o3SensorAnalogValue3, "\t",
                count += 1
                time.sleep(5)  # Every five seconds
                o3SensorAnalogValue4 = MQ131.readadc(adcnum, CONSTANTS.SPICLK, CONSTANTS.SPIMOSI, CONSTANTS.SPIMISO, CONSTANTS.SPICS)
                # print "The Analog to Digital value4 ",
                # print  o3SensorAnalogValue4, "\t",
                count += 1
                time.sleep(5)  # Every five seconds
                o3SensorAnalogValue5 = MQ131.readadc(adcnum, CONSTANTS.SPICLK, CONSTANTS.SPIMOSI, CONSTANTS.SPIMISO, CONSTANTS.SPICS)
                # print "The Analog to Digital value5 ",
                # print  o3SensorAnalogValue5, "\t",
                count += 1

                # Average reading
                o3SensorAnalogValueAvg = (
                                         o3SensorAnalogValue1 + o3SensorAnalogValue2 + o3SensorAnalogValue3 + o3SensorAnalogValue4 + o3SensorAnalogValue5) / count
                print("The Analog to Digital value avg ", end=' ')
                print(o3SensorAnalogValueAvg, "\t", end=' ')
                count = 0  # reset counter

                # Voltage from average reading
                voltage = MQ131.voltageADC(o3SensorAnalogValueAvg)

                # Get the Rs value (O3 concentrations of gases) from the average of the 5 readings
                Rs = MQ131.MQResistance(o3SensorAnalogValueAvg, MQ131.RL_MQ131)

                # Get the Ro (Clean Air) value from the average of the 5 readings
                Ro = MQ131.MQCalibration(Rs)

                # Get Ratio from the Rs and Ro values
                Rs_Ro_Ratio = MQ131.RsRoRatio(Rs, Ro)

                # Get the ppm value from the average of the 5 readings
                ppm = MQ131.calculatePPM(Rs_Ro_Ratio, Ro)

                # Convert the ppm value to ppb value
                ppb = MQ131.convertPPMToPPB(ppm)

                print("The PPB ", end=' ')
                print(ppb, "\t", end=' ')

                generate_ozone_MQ131(voltage, Rs, Ro, Rs_Ro_Ratio, ppb)

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