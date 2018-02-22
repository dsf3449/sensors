import os
import sys
import argparse
import time
import sched

import RPi.GPIO as GPIO

from sensors.common.logging import configure_logger
from sensors.config import Config, ConfigurationError
from sensors.config.constants import *

from sensors.raspi.constants import *


def generate_observations_minute():
    config = Config().config
    logger = configure_logger(config)
    logger.debug("Begin generate_observations_minute...")
    thing = config[CFG_THING]
    foi_id = thing.location_id

    # Iterate over sensors and generate observations
    sensors = config[CFG_SENSORS]
    logger.debug("Iterating over {0} sensors...".format(len(sensors)))
    for s in sensors:
        logger.debug(str(s))
        logger.debug("Calling generate_observations for sensor type {0}...".format(s.typ))
        observations = s.generate_observations(feature_of_interest_id=foi_id)
        logger.debug("Enqueing observations...")
        [logger.debug(str(o)) for o in observations]


def sample():
    logger.debug("About to start scheduler...")
    s = sched.scheduler(time.time, time.sleep)

    try:
        while True:
            # Schedule event to run every minute
            logger.debug("Test Sampler: scheduling observation sampling...")
            s.enter(SAMPLE_INTERVAL_ONE_MINUTE,
                    SCHEDULE_PRIORITY_DEFAULT,
                    generate_observations_minute)
            # Run scheduled events
            logger.debug("Test Sampler: Running scheduler...")
            s.run()
            logger.debug("Test Sampler: End of iteration.")
    except:
        pass
    finally:
        logger.info("Test Sample: exiting.")


def main():
    parser = argparse.ArgumentParser(description='Test Raspberry Pi sensors')
    parser.add_argument('-c', '--config', type=str, required=False)
    parser.add_argument('-t', '--configtest', action='store_true')
    args = parser.parse_args()

    if args.config is not None:
        assert (os.path.exists(args.config))
        os.environ[ENV_YAML_PATH] = args.config

    if args.configtest:
        try:
            c = Config().config
        except ConfigurationError as e:
            print("Configuration is invalid: {0}".format(e.message))
            sys.exit(1)
        print("Configuration is valid.")
        sys.exit(0)

    config = Config().config
    global logger
    logger = configure_logger(config)

    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        sample()
    except KeyboardInterrupt:
        GPIO.cleanup()
    finally:
        logger.info("Raspberry Pi sensor: exiting.")
