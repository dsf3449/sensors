from __future__ import print_function
import time
import sys
import signal
import atexit
from upm import pyupm_hka5 as sensorObj

def main():
    # Instantiate a HKA5 sensor on uart 0.  We don't use the set or
    # reset pins, so we pass -1 for them.
    sensor = sensorObj.HKA5(0, -1, -1)

    ## Exit handlers ##
    # This function stops python from printing a stacktrace when you hit control-C
    def SIGINTHandler(signum, frame):
        raise SystemExit

    # This function lets you run code on exit
    def exitHandler():
        print("Exiting")
        sys.exit(0)

    # Register exit handlers
    atexit.register(exitHandler)
    signal.signal(signal.SIGINT, SIGINTHandler)

    # update once every 2 seconds and output data
    while (True):
        sensor.update()

        print("PM 1  :", end=' ')
        print(sensor.getPM1(), end=' ')
        print(" ug/m3")

        print("PM 2.5:", end=' ')
        print(sensor.getPM2_5(), end=' ')
        print(" ug/m3")

        print("PM 10 :", end=' ')
        print(sensor.getPM10(), end=' ')
        print(" ug/m3")

        print()
        time.sleep(2)

if __name__ == '__main__':
    main()