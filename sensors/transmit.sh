#!/bin/sh
export CGIST_URL="https://sensorthings.southcentralus.cloudapp.azure.com/device/api/v1.0/CreateObservations"
export CGIST_AUTH_URL="https://sensorthings.southcentralus.cloudapp.azure.com/device/api/auth/login"
export JWT_ID="1111111-1111-1111-1111-111111111111"
export JWT_KEY="222222-2222-2222-2222-222222222222"
/home/pi/sensors/transmit.py > /var/log/sensor_transmit.log 2>&1