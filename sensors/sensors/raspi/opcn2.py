#!/usr/bin/python

import spidev
import opc
from time import sleep

# Open a SPI connection on CE0
spi = spidev.SpiDev()
spi.open(0, 0)

# Set the SPI mode and clock speed
spi.mode = 1
spi.max_speed_hz = 500000

alpha = opc.OPCN2(spi)

try:
    # Read the information string
    print (alpha.read_info_string())
    while True:
        # Turn on the OPC
        alpha.on()

        # Read the PM data
        print ("OPC PM Data")
        for key, value in alpha.pm().items():
            print ("Key: {}\tValue: {}".format(key, value))

        sleep(15)

except KeyboardInterrupt:
    # Turn the opc OFF
    alpha.off()

