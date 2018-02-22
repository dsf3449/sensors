import logging

from sensors.common import constants
from sensors.config.constants import CFG_LOGGING_LOGGER_PATH
from sensors.config import Config

loggers = {}


def get_instance():
    return configure_logger(Config.config)


def configure_logger(c):
    global loggers

    logger = loggers.get(constants.LOGGER_NAME)
    if not logger:
        logger_path = c[CFG_LOGGING_LOGGER_PATH]

        logger = logging.getLogger(constants.LOGGER_NAME)
        logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(logger_path)
        fh.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

        loggers[constants.LOGGER_NAME] = logger

    return logger
