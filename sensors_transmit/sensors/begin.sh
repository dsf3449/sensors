#!/bin/bash
cd /usr/src/app/sensors

while [[ -z "${YAML_DL_PATH}" ]];
do
	echo "No sensor.yml is defined.  Please set YAML_DL_PATH in balenaCloud."
	sleep 5
done

wget "$YAML_DL_PATH"

sensor_transmit &
sleep 10
tail -f /var/log/sensor.log
