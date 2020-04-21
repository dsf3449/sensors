import os
import sys
import argparse
import time
import sched
import multiprocessing as mp

import RPi.GPIO as GPIO

import sensors.persistence.spool as spool
from sensors.common.logging import configure_logger
from sensors.config import Config, ConfigurationError
from sensors.common.constants import *

from sensors.raspi.constants import *


def generate_observations_minute(queue):
    config = Config().config
    logger = configure_logger(config)
    logger.debug("Begin generate_observations_minute...")
    thing = config[CFG_THING]

    # Iterate over sensors and generate observations
    sensors = config[CFG_SENSORS]
    logger.debug("Iterating over {0} sensors...".format(len(sensors)))
    for s in sensors:
        logger.debug(str(s))
        logger.debug("Calling generate_observations for sensor type {0}...".format(s.typ))
        observations = s.generate_observations()
        logger.debug("Enqueing observations...")
        [queue.put(o) for o in observations]


def sample():
    try:
        # Start process to send data to
        mp.set_start_method('spawn')
        logger.debug("About to create queue...")
        q = mp.Queue()
        logger.debug("About to create process...")
        p = mp.Process(target=spool.spool_data, args=(q,))
        logger.debug("About to start process...")
        p.start()
        logger.debug("About to start scheduler...")
        s = sched.scheduler(time.time, time.sleep)

        # Get the schedule interval from the env var set by balenaCloud
        sample_interval = os.environ.get('SAMPLE_INTERVAL')
        if sample_interval is None:
            logger.info("SAMPLE_INTERVAL is not defined. We will default to 1 minute unless this is set.")
            sample_interval = 60
        else:
            sample_interval = float(sample_interval)

        while True:
            # Schedule event to run a variable amount of time
            logger.debug("Raspberry Pi Sampler: scheduling observation sampling with delay of {0} seconds...".
                         format(sample_interval))
            s.enter(sample_interval,
                    SCHEDULE_PRIORITY_DEFAULT,
                    generate_observations_minute,
                    argument=(q,))
            # Run scheduled events
            logger.debug("Raspberry Pi Sampler: Running scheduler...")
            s.run()
            logger.debug("Raspberry Pi Sampler: End of iteration.")
    except:
        logger.exception("Raspberry Pi Sampler: Exception caught in sample()")
    finally:
        logger.info("Raspberry Pi Sampler: exiting.")


def main():
    parser = argparse.ArgumentParser(description='Raspberry Pi sampler for LEaRN project')
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
    logger.info("Raspberry Pi Sampler: entering.")

    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        sample()
    except KeyboardInterrupt:
        GPIO.cleanup()
    finally:
        logger.info("Raspberry Pi Sampler: exiting.")
