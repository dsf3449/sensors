import argparse
import datetime
import multiprocessing as mp
import random
import sched
import time
import os

import sensors.persistence.spool as spool
from sensors.common.logging import configure_logger
from sensors.domain.observation import Observation


SAMPLE_INTERVAL_ONE_MINUTE = 60
SCHEDULE_PRIORITY_DEFAULT = 1


# Configure logging
logger = configure_logger()


next_date = None
di = None


def _rand():
    return random.uniform(1.23, 123.45)


def _next_date():
    global next_date
    if next_date is None:
        next_date = datetime.datetime.now().isoformat()
        return next_date
    next_date = next_date + di
    return next_date


def generate_observation(featureOfInterestId, datastreamId, phenomenonTime,
                         result, parameters):
    logger.debug("generate_observation: {0}".format(phenomenonTime.isoformat()))
    o = Observation()
    o.featureOfInterestId = featureOfInterestId
    o.datastreamId = datastreamId
    o.phenomenonTime = phenomenonTime.isoformat()
    o.result = result
    o.set_parameters(**parameters)

    return o


def generate_ozone_MQ131():
    foi_id = os.environ.get("CGIST_FOI_ID", "c81a4920-100b-11e7-987b-9b2f50364984")
    ds_id = os.environ.get("CGIST_DS_ID_MQ131", "1e34fad0-100c-11e7-987b-9b2f50364984")
    parameters = {"voltage": str(_rand()),
                  "Rs": str(_rand()),
                  "Ro": str(_rand()),
                  "Rs_Ro_Ratio": str(_rand())}
    return generate_observation(foi_id, ds_id,
                                _next_date(),
                                str(_rand()), parameters)


def generate_observations_minute(queue):
    logger.debug("Generating O3 observation...")
    o = generate_ozone_MQ131()
    logger.debug("Queuing observation {0}...".format(str(o)))
    queue.put(o)
    logger.debug("done")


def sample(start_date=datetime.datetime.now().isoformat(),
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
        p = mp.Process(target=spool.spool_data, args=(q,))
        p.start()

        s = sched.scheduler(time.time, time.sleep)

        while True:
            # Schedule event to run every minute
            logger.debug("Sampler: scheduling observation sampling...")
            s.enter(SAMPLE_INTERVAL_ONE_MINUTE,
                    SCHEDULE_PRIORITY_DEFAULT,
                    generate_observations_minute,
                    argument=(q,))
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
    args = parser.parse_args()

    start_date = datetime.datetime(year=args.startdate[0], month=args.startdate[1], day=args.startdate[2],
                                   hour=args.startdate[3], minute=args.startdate[4])
    print("Start date: {0}".format(str(start_date)))

    date_interval = datetime.timedelta(minutes=args.dateint)
    print("Date interval: {0} minutes".format(str(date_interval)))

    sample(start_date=start_date, date_interval=date_interval)
