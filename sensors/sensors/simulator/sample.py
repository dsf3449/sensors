import datetime
import multiprocessing as mp
import random
import sched
import time

import sensors.persistence.spool as spool
from sensors.common.logging import configure_logger
from sensors.domain.observation import Observation

SAMPLE_INTERVAL_ONE_MINUTE = 5
SCHEDULE_PRIORITY_DEFAULT = 1


# Configure logging
logger = configure_logger()


def _rand():
    return random.uniform(1.23, 123.45)


def generate_observation(featureOfInterestId, datastreamId, phenomenonTime,
                         result, parameters):
    o = Observation()
    o.featureOfInterestId = featureOfInterestId
    o.datastreamId = datastreamId
    o.phenomenonTime = phenomenonTime
    o.result = result
    o.set_parameters(**parameters)

    return o


def generate_ozone_MQ131(featureOfInterestId, datastreamId):
    parameters = {"voltage": str(_rand()),
                  "Rs": str(_rand()),
                  "Ro": str(_rand()),
                  "Rs_Ro_Ratio": str(_rand())}
    return generate_observation(featureOfInterestId, datastreamId,
                                datetime.datetime.now().isoformat(),
                                str(_rand()), parameters)


def generate_observations_minute(queue):
    logger.debug("Generating O3 observation...")
    o = generate_ozone_MQ131("c81a4920-100b-11e7-987b-9b2f50364984",
                             "1e34fad0-100c-11e7-987b-9b2f50364984")
    logger.debug("Queuing observation {0}...".format(str(o)))
    queue.put(o)
    logger.debug("done")


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
