import sched
import time

from sensors.common.logging import configure_logger
from sensors.config import Config, ConfigurationError
from sensors.config.constants import *
from sensors.persistence.sqlite import SqliteRepository
from sensors.transport import AuthenticationException, TransmissionException

SCHEDULE_PRIORITY_DEFAULT = 1


def main():
    config = Config().config
    global logger
    logger = configure_logger(config)

    repo = SqliteRepository(config)
    s = sched.scheduler(time.time, time.sleep)

    while True:
        try:
            transports = config[CFG_TRANSPORTS]
            logger.debug("Transmitter: scheduling network transmissions for {0} transports...".format(len(transports)))
            for t in transports:
                s.enter(t.transmit_interval_seconds(),
                        SCHEDULE_PRIORITY_DEFAULT,
                        t.transmit,
                        argument=(repo,))
                logger.debug("Transmitter: Running scheduler...")
                s.run()
                logger.debug("Transmitter: End of iteration.")
        except KeyboardInterrupt:
            break
        except AuthenticationException as ae:
            logger.error("Transmitter: {0]".format(ae.message))
        except TransmissionException as te:
            logger.error("Transmitter: {0}".format(te.message))
        finally:
            pass
    logger.info("Transmitter: exiting.")
