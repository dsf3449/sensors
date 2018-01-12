import logging

from sensors.common import constants
from sensors.config.constants import CFG_LOGGING_LOGGER_PATH


def configure_logger(c):
    logger = get_logger()
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(c[CFG_LOGGING_LOGGER_PATH])
    fh.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def get_logger():
    return logging.getLogger(constants.LOGGER_NAME)
