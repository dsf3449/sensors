#!/bin/bash

SD_YML_LOC=/media/$USER/rootfs/home/pi/
YML=sensor.yml
YML_LOC=yml
YML_PATH=$YML_LOC/$YML

#################################################################
# Replace sensor.yml
#################################################################
echo "Replacing default sensor.yml"

cd yml
FILE=$(ls | sort -n | head -1)
echo "YML used -> $FILE"

mv $FILE $YML
cd ..

mv $YML_PATH $SD_YML_LOC

echo "#################################################################"
echo "sensor.yml:"
echo
cat $SD_YML_LOC$YML
echo "#################################################################"
