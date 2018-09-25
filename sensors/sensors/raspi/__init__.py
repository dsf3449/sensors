
def import_raspi_gpio():
    """ Catch ModuleNotFoundError and return None if RPi.GPIO is
        not installed (e.g. if we are running the simulator on a
        non-RPi platform)
    """
    try:
        import RPi.GPIO as GPIO
        return GPIO
    except ModuleNotFoundError:
        return None


def import_adafruit_adc():
    """ Catch ModuleNotFoundError and return None if Adafruit_ADS1x15 is
        not installed (e.g. if we are running the simulator on a
        non-RPi platform)
    """
    try:
        import Adafruit_ADS1x15 as adafruit_adc
        return adafruit_adc
    except ModuleNotFoundError:
        return None


def import_spidev():
    """ Catch ModuleNotFoundError and return None if spidev is
            not installed (e.g. if we are running the simulator on a
            non-RPi platform)
        """
    try:
        import spidev
        return spidev
    except ModuleNotFoundError:
        return None
