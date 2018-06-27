import logging

LOGGER_NAME = 'sensors'
DEFAULT_LOGGER_PATH = '/var/log/sensor.log'
DEFAULT_LOGGER_LEVEL_CONSOLE = 'DEBUG'
DEFAULT_LOGGER_LEVEL_FILE = 'INFO'
DEFAULT_DB_PATH = '/var/spool/sensor.sqlite'

ENV_YAML_PATH = 'LEARN_YAML_PATH'

# YAML config elements

# Common elements
CFG_ID = 'id'
CFG_NAME = 'name'
CFG_TYPE = 'type'
CFG_PROPERTIES = 'properties'
CFG_LOCATION_ID = 'location_id'
CFG_FOI_ID = 'feature_of_interest_id'
CFG_DATASTREAM_ID = 'datastream_id'
CFG_URL = 'url'
CFG_ENABLED = 'enabled'

CFG_SIMULATOR = 'simulator'

CFG_LOGGING = 'logging'
CFG_LOGGING_LOGGER_PATH = 'logger_path'
CFG_LOGGING_LEVEL_CONSOLE = 'level_console'
CFG_LOGGING_LEVEL_FILE = 'level_file'

CFG_LOGGING_LEVELS = {'CRITICAL': logging.CRITICAL,
                      'ERROR': logging.ERROR,
                      'WARNING': logging.WARNING,
                      'INFO': logging.INFO,
                      'DEBUG': logging.DEBUG,
                      'NOTSET': logging.NOTSET}

CFG_SPOOLER = 'spooler'
CFG_SPOOLER_DB_PATH = 'db_path'

CFG_THING = 'thing'

CFG_SENSORS = 'sensors'
CFG_SENSOR = 'sensor'
CFG_SENSOR_TYPE_MQ131 = 'mq131'
CFG_SENSOR_TYPE_DHT11 = 'dht11'
CFG_SENSOR_TYPE_SM50 = 'sm50'
CFG_SENSOR_TYPE_SEN0177 = 'sen0177'

CFG_SENSOR_ADC_MCP3002 = 'mcp3002'
CFG_SENSOR_ADC_ADS1015 = 'ads1015'

CFG_PROPERTY_ADC = 'adc'

CFG_PROPERTIES = 'properties'
CFG_OBSERVED_PROPERTIES = 'observed_properties'
CFG_OBSERVED_PROPERTY = 'observed_property'
CFG_OBSERVED_PROPERTY_OZONE = 'ozone'
CFG_OBSERVED_PROPERTY_AIR_TEMP = 'air_temperature'
CFG_OBSERVED_PROPERTY_RH = 'relative_humidity'
CFG_OBSERVED_PROPERTY_PM = 'particulate_matter'

CFG_TRANSPORTS = 'transports'
CFG_TRANSPORT = 'transport'
CFG_TRANSPORT_TYPE_HTTPS = 'https'
CFG_TRANSPORT_HTTPS_AUTH_URL = 'auth_url'
CFG_TRANSPORT_HTTPS_JWT_ID = 'jwt_id'
CFG_TRANSPORT_HTTPS_JWT_KEY = 'jwt_key'
CFG_TRANSPORT_HTTPS_TRANSMIT_INTERVAL_SEC = 'transmit_interval_seconds'
CFG_TRANSPORT_HTTPS_VERIFY_SSL = 'verify_ssl'
CFG_TRANSPORT_HTTPS_JWT_TTL = 'jwt_token_ttl_minutes'
