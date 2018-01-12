import argparse
import datetime
import multiprocessing as mp
import sched
import time
import os
import sys

import sensors.persistence.spool as spool
from sensors.common.logging import configure_logger
from sensors.config import Config, ConfigurationError
from sensors.config.constants import *


SAMPLE_INTERVAL_ONE_MINUTE = 60
SCHEDULE_PRIORITY_DEFAULT = 1


# Configure logging
logger = None


next_date = None
di = None


def _next_date():
    global next_date
    if next_date is None:
        next_date = datetime.datetime.now().isoformat()
        return next_date
    next_date = next_date + di
    return next_date


def generate_observations_minute(config, queue):
    thing = config[CFG_THING]
    foi_id = thing.location_id

    sensors = config[CFG_SENSORS]
    # Iterate over sensors and generate observations
    for s in sensors:
        observations = s.generate_observations(phenomenon_time=_next_date(),
                                               feature_of_interest_id=foi_id)
        [queue.put(o) for o in observations]


def sample(config,
           start_date=datetime.datetime.now().isoformat(),
           date_interval=datetime.timedelta(minutes=1)):
    global next_date
    global di

    next_date = start_date
    di = date_interval

    logger.info("Start date: {0}, date interval: {1} minutes".format(str(next_date), str(di)))

    p = None
    try:
        # Start process to send data to
        mp.set_start_method('spawn')
        q = mp.Queue()
        p = mp.Process(target=spool.spool_data, args=(config, q))
        p.start()

        s = sched.scheduler(time.time, time.sleep)

        while True:
            # Schedule event to run every minute
            logger.debug("Sampler: scheduling observation sampling...")
            s.enter(SAMPLE_INTERVAL_ONE_MINUTE,
                    SCHEDULE_PRIORITY_DEFAULT,
                    generate_observations_minute,
                    argument=(config, q))
            # Run scheduled events
            logger.debug("Sampler: Running scheduler...")
            s.run()
            logger.debug("Sampler: End of iteration.")
    except:
        pass
    finally:
        if p:
            p.join()
        logger.info("Simulator: exiting.")


def main():
    parser = argparse.ArgumentParser(description='Simulate a sensor')
    parser.add_argument('-d', '--startdate', nargs=5, type=int,
                        default=[2017, 1, 1, 0, 0],
                        help='Start date for data: YYYY MM DD HH MM')
    parser.add_argument('-i', '--dateint', type=int,
                        default=1,
                        help='Number of minutes between subsequent data')
    parser.add_argument('-c', '--config', type=str, required=False)
    parser.add_argument('-t', '--configtest', action='store_true')
    args = parser.parse_args()

    if args.config is not None:
        assert(os.path.exists(args.config))
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

    start_date = datetime.datetime(year=args.startdate[0], month=args.startdate[1], day=args.startdate[2],
                                   hour=args.startdate[3], minute=args.startdate[4])
    print("Start date: {0}".format(str(start_date)))

    date_interval = datetime.timedelta(minutes=args.dateint)
    print("Date interval: {0} minutes".format(str(date_interval)))

    sample(config, start_date=start_date, date_interval=date_interval)
