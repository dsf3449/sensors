from sensors.raspi import import_spidev
SPIDEV = import_spidev()
import opc
from time import sleep

from sensors.domain.sensor import ParticulateMatterSensor
from sensors.common.constants import *


class OPCN2(ParticulateMatterSensor):
    NAME = CFG_SENSOR_TYPE_OPCN2

    SPI_BUS = 0
    SPI_DEVICE = 0
    SPI_MODE = 1
    SPI_SPEED_HZ = 500000

    def _particulates(self):
        spi = None
        alphasense = None
        try:
            # Setup SPI device
            spi = SPIDEV.SpiDev()
            spi.open(OPCN2.SPI_BUS, OPCN2.SPI_DEVICE)
            spi.mode = OPCN2.SPI_MODE
            spi.max_speed_hz = OPCN2.SPI_SPEED_HZ

            alphasense = opc.OPCN2(spi, max_cnxn_retries=15)

            # Turn the opc ON and wait before reading data
            alphasense.on()
            sleep(1)

            # Read the PM data
            pm = alphasense.pm()
            result = float(pm['PM2.5'])
            parameters = {"pm1": str(pm['PM1']),
                          "pm10": str(pm['PM10'])}

            return result, parameters
        finally:
            if alphasense is not None:
                alphasense.off()
            if spi is not None:
                spi.close()

    def __init__(self, typ, *args, **kwargs):
        super().__init__(typ, *args, **kwargs)
