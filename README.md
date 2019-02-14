# Firmware for Raspberry Pi sensors used in [Lafayette Engagement and
  Research Network](https://learnlafayette.com/) air quality sensor
  network.

Uses a simple and flexible YAML-based configuration to give each
sensor its own personality, regardless of the sensors installed.  This
configuration file is used to enable the drivers specific to each kind
of supported sensor (e.g. Alphasense OPN-N2, Aeroqual SM50), and to
enable one or more network transports (e.g. SensorThings over HTTPS,
Azure IoT Hub, etc.).  See below for an example configuration file.

Example configuration
```
simulator:
  enabled: true
logging:
  logger_path: /var/log/sensor.log
  level_console: INFO
  level_file: DEBUG
spooler:
  db_path: /var/spool/mqueue/sensor.sqlite
thing:
  id: 5474a427-f565-4233-8f82-a8178534b150
  location_id: f5610fb9-1556-42d8-862c-1d290a9b5c58
sensors:
  - type: mq131
    observed_properties:
      - name: ozone
        datastream_id: 1af6b695-07c0-4024-aeb8-4ddf64dbf458
  - type: dht11
    multidatastream_id: 1874209f-72b0-4d7f-993c-2707fa01ccd2
    observed_properties:
      - air_temperature
      - relative_humidity
transports:
  - type: https
    properties:
      auth_url: https://myservice.com/auth
      url: https://myservice.com/v1.0/
      jwt_id: 6d770f60-9912-4545-9d3c-9e8dcf4a0dad
      jwt_key: faac9ce4-fd2d-476b-9984-aee2b71dfc8e
      jwt_token_ttl_minutes: 15
      transmit_interval_seconds: 15
      verify_ssl: false
```


