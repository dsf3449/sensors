import logging

from sensors.common import constants


def configure_logger():
    logger = get_logger()
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(constants.LOGGER_FILE)
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
