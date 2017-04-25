#!/bin/sh

export CGIST_FOI_ID="e31a0460-26a2-11e7-bcad-97b506bd22c3"
export CGIST_DS_ID_MQ131="ad85a0b0-26a3-11e7-bcad-97b506bd22c3"
/home/pi/sensors/sensors/raspi/sample.py > /var/log/sensor_spool.log 2>&1
