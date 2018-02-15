
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
