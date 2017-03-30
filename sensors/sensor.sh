#!/bin/sh

export FEATURE_OF_INTEREST_ID="d3d71eaa-6f6c-4e5b-bb52-3ce2adea0b3e"
export DATASTREAM_ID="4b007564-51df-4e41-95e5-02b300e36af1"
export JWT_ID="4580407a-85f3-4526-9340-59909bf2614f"
export JWT_KEY="8353cda3-06cf-4dd1-91e0-f8eeedbceb25"
/home/pi/sensor.py > /home/pi/sensor.log 2>&1
