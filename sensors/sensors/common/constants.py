import os

LOGGER_NAME = "sensors"
LOGGER_FILE = os.environ.get("LOGGER_PATH", "/tmp/sensor.log")

DB_PATH = os.environ.get("DB_PATH", "/tmp/sensor.sqlite")

# change these as desired
SPICLK = 11 #18
SPIMOSI = 10 #17
SPIMISO = 9 #21
SPICS = 8 #22

# Equation values
RL_MQ131 = 0.679  # MQ131 Sainsmart Resistor Load value

SAMPLE_INTERVAL_ONE_MINUTE = 60
SCHEDULE_PRIORITY_DEFAULT = 1
