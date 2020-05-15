import json

import spidev
import opc
from time import sleep

SPI_BUS = 0
SPI_DEVICE = 0
SPI_MODE = 1
SPI_SPEED_HZ = 500000


def main():
    spi = None
    alphasense = None
    try:
        # Setup SPI device
        spi = spidev.SpiDev()
        spi.open(SPI_BUS, SPI_DEVICE)
        spi.mode = SPI_MODE
        spi.max_speed_hz = SPI_SPEED_HZ

        alphasense = opc.OPCN2(spi, max_cnxn_retries=15)

        # Turn the opc ON and wait before reading data
        alphasense.on()
        sleep(10)

        # Read the PM data, throwing out the first two readings as these seem to always be
        # zero or a very small number.  Wait between readings just in case that matters.
        alphasense.pm()
        sleep(2)
        alphasense.pm()
        sleep(2)
        pm = alphasense.pm()
        result = {'PM2.5': float(pm['PM2.5']), 'PM1': float(pm['PM1']), 'PM10': float(pm['PM10'])}
        print(json.dumps(result))
    finally:
        if alphasense is not None:
            alphasense.off()
        if spi is not None:
            spi.close()
