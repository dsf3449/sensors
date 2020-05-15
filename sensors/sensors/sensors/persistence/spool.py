from sensors.config import Config
from sensors.common.logging import configure_logger
from sensors.domain.observation import Observation
from sensors.domain.multiobservation import MultiObservation
from sensors.persistence.sqlite import SqliteRepository


def spool_data(q):
    config = Config().config
    logger = configure_logger(config)
    logger.info("Spooler: entering.")
    repo = SqliteRepository(config)
    while True:
        try:
            logger.debug("Spooler: getting from queue...")
            obs = q.get()
            logger.debug("Spooler: received observation: {0}".format(str(obs)))
            if isinstance(obs, Observation):
                repo.create_observation(obs)
            elif isinstance(obs, MultiObservation):
                repo.create_multiobservation(obs)
            else:
                raise TypeError("Observation of type {0} is unknown".format(obs.__class__.__name__))
            logger.debug("Spooler: observation stored in database")
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.exception("Spooler: caught exception: {0}".format(str(e)))
        finally:
            pass
    logger.info("Spooler: exiting.")
