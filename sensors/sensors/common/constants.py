import os

LOGGER_NAME = "sensors"
LOGGER_FILE = os.environ.get("LOGGER_PATH", "/val/log/sensor.log")

DB_PATH = os.environ.get("DB_PATH", "/var/spool/mqueue/sensor.sqlite")

# change these as desired
SPICLK = 11 #18
SPIMOSI = 10 #17
SPIMISO = 9 #21
SPICS = 8 #22

vref = 3.3 * 1000 # V-Ref in mV (Vref = VDD for the MCP3002)
resolution = 2**10 # for 10 bits of resolution
calibration = 38 # in mV, to make up for the precision of the components

# Equation values
pcCurve = [42.84561841, -1.043297135] # MQ131 O3 coordinates on curve
RL_MQ131 = 0.679                      # MQ131 Sainsmart Resistor Load value
READ_SAMPLE_VALUES = 5                # Number of samples to read to get average
READ_SAMPLE_TIME = 0.5                # Reads sample data in milliseconds

SAMPLE_INTERVAL_ONE_MINUTE = 60
SCHEDULE_PRIORITY_DEFAULT = 1
