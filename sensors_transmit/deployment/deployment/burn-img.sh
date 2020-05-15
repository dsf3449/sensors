#!/bin/bash

#################################################################
# VARS
#################################################################
BS=4M
IF=learn-rpi-1_0-preshrunk.img
IF_LOC=img
IF_PATH=$IF_LOC/$IF
OF_PATH=/dev/sdb
USER=$1
SD_LOC=/media/$USER/*


#################################################################
# Unmount
#################################################################
echo "Unmounting SD"
umount $SD_LOC

#################################################################
# Burn IMG
#################################################################
echo "Burning IMG to SD"
sudo dd bs=$BS if=$IF_PATH of=$OF_PATH status=progress conv=fsync

echo "SD imaging complete"
echo







