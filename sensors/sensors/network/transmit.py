import os, argparse
import sched
import time

from sensors.common.logging import configure_logger
from sensors.config import Config, ConfigurationError
from sensors.common.constants import *
from sensors.persistence.sqlite import SqliteRepository
from sensors.transport import AuthenticationException, TransmissionException

SCHEDULE_PRIORITY_DEFAULT = 1


def main():
    parser = argparse.ArgumentParser(description='Test Raspberry Pi sensors')
    parser.add_argument('-c', '--config', type=str, required=False)
    args = parser.parse_args()

    if args.config is not None:
        assert (os.path.exists(args.config))
        os.environ[ENV_YAML_PATH] = args.config

    config = Config().config
    global logger
    logger = configure_logger(config)
    logger.info("Transmitter: entering.")

    repo = SqliteRepository(config)
    s = sched.scheduler(time.time, time.sleep)

    while True:
        try:
            # Get the transmit interval from the env var set by balenaCloud
            transmit_interval = os.environ.get('TRANSMIT_INTERVAL')
            if transmit_interval is None:
                logger.info("Transmitter: TRANSMIT_INTERVAL is not defined. We will default to 15 seconds unless this is set.")
                transmit_interval = 15
            else:
                transmit_interval = float(transmit_interval)

            transports = config[CFG_TRANSPORTS]
            logger.debug("Transmitter: scheduling network transmissions for {0} transports...".format(len(transports)))
            for t in transports:
                s.enter(transmit_interval,
                        SCHEDULE_PRIORITY_DEFAULT,
                        t.transmit,
                        argument=(repo,))
                logger.debug("Transmitter: Running scheduler...")
                s.run()
                logger.debug("Transmitter: End of iteration.")
        except KeyboardInterrupt:
            break
        except AuthenticationException as ae:
            logger.exception("Transmitter: {0}".format(ae.message))
        except TransmissionException as te:
            logger.exception("Transmitter: {0}".format(te.message))
        finally:
            pass
    logger.info("Transmitter: exiting.")
