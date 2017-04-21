import os

LOGGER_NAME = "sensors"
LOGGER_FILE = os.environ.get("LOGGER_PATH", "/tmp/sensor.log")

DB_PATH = os.environ.get("DB_PATH", "/tmp/sensor.sqlite")
