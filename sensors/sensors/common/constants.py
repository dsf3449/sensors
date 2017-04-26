import os

LOGGER_NAME = "sensors"
LOGGER_FILE = os.environ.get("LOGGER_PATH", "/var/log/sensor.log")

DB_PATH = os.environ.get("DB_PATH", "/var/spool/mqueue/sensor.sqlite")

