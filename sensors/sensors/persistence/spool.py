from sensors.config import Config
from sensors.common.logging import configure_logger
from sensors.persistence.sqlite import SqliteRepository


def spool_data(q):
    config = Config().config
    logger = configure_logger(config)
    repo = SqliteRepository(config)
    while True:
        try:
            logger.debug("Spooler: getting from queue...")
            obs = q.get()
            logger.debug("Spooler: received observation: {0}".format(str(obs)))
            repo.create_observation(obs)
            logger.debug("Spooler: observation stored in database")
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.info("Spooler: caught exception: {0}".format(str(e)))
        finally:
            pass
    logger.info("Spooler: exiting.")
