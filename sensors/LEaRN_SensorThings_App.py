###  CGI Digital Services - LEaRN 
###  March 2017
### Application to read O3 Senser (MQ315) from the Raspberry Pi 3 Rev. B 
### Converts the analog value to digital value with the MCP3002 chip
### Once we have that value, it will convert it to an equation to get the parts per billion (ppb) value
### Finally, the value will be stored in a JSON object to POST a request from the SensorThings API that is in an Microsoft Azure instance
### V0.0.1

#!/usr/bin/python

import os
import glob
import datetime
import time
import json
import math
import requests

import RPi.GPIO as GPIO

vref = 3.3 * 1000 # V-Ref in mV (Vref = VDD for the MCP3002)
resolution = 2**10 # for 10 bits of resolution
calibration = 38 # in mV, to make up for the precision of the components

#Logical GPIO numbering schema
GPIO.setmode(GPIO.BCM)

# change these as desired
SPICLK = 11 #18
SPIMOSI = 10 #17
SPIMISO = 9 #21
SPICS = 8 #22

# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

# Equation values
pcCurve = [42.84561841, -1.043297135] # MQ131 O3 coordinates on curve
#Ro = 10000                            # Ro is initialized to 10 kilo ohms
RL_MQ131 = 0.679                      # MQ131 Sainsmart Resistor Load value
READ_SAMPLE_VALUES = 5                # Number of samples to read to get average
READ_SAMPLE_TIME = 0.5                # Reads sample data in milliseconds

# SensorThings API in Microsoft Azure instance
URL = "http://sensorthings.southcentralus.cloudapp.azure.com:8080/device/api/v1.0/Observations"

# JSON id / values to send to SensorThings API standard
JSON_TEMPLATE = '''{{"FeatureOfInterest":{{"@iot.id":"{featureOfInterestId}"}},
  "Datastream":{{"@iot.id":"{datastreamId}"}},
  "phenomenonTime":"{phenomenonTime}",
  "parameters":{{{parametersStr}}},
  "result":"{result}"
}}'''

# POST to SensorThings API after average ppb is calculated
def post_observation(featureOfInterestId,
                     datastreamId,
                     phenomenonTime,
                     result,
                     parameters={}):
    parametersStr = ",".join(['"{k}":"{v}"'.format(k=e[0], v=e[1]) for e in parameters.items()])
    json = JSON_TEMPLATE.format(featureOfInterestId=featureOfInterestId,
                                datastreamId=datastreamId,
                                phenomenonTime=phenomenonTime,
                                result=result,
                                parametersStr=parametersStr)
    print("Posting new data {0}".format(json))
    headers = {'Content-Type': 'application/json'}
    r = requests.post(URL, headers=headers, data=json)
    print("Status code was {0}".format(r.status_code))
    location = r.headers['Location']
    print("Location: {0}".format(location))

# read SPI data from MCP3002 chip, 2 possible adc's (0 thru 1)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
    if ((adcnum > 1) or (adcnum < 0)):
        return -1
    GPIO.output(cspin, True)
    
    GPIO.output(clockpin, False)  # start clock low
    GPIO.output(cspin, False)     # bring CS low
    
    commandout = adcnum << 1
    commandout |= 0x0D  # start bit + single-ended bit + MSBF bit
    commandout <<= 4    # we only need to send 4 bits here
    
    for i in range(4):
        if (commandout & 0x80):
            GPIO.output(mosipin, True)
        else:
            GPIO.output(mosipin, False)
        commandout <<= 1
        GPIO.output(clockpin, True)
        GPIO.output(clockpin, False)
    
    adcout = 0
    
    # read in one null bit and 10 ADC bits
    for i in range(11):
        GPIO.output(clockpin, True)
        GPIO.output(clockpin, False)
        adcout <<= 1
        if (GPIO.input(misopin)):
            adcout |= 0x1
    GPIO.output(cspin, True)
    
    adcout /= 2  # first bit is 'null' so drop it
    return adcout

# Calculates voltage from Analog to Digital Converter in medium voltage (mV)
def voltageADC(readadc):
    voltage = int(round(((readadc * vref * 2) / resolution),0))+ calibration
    return voltage

# Calculates vrl for resistance of sensor equation
#def vrl(adc):
#    vrl = adc * 5 / 4096.0
#    return vrl

# Calculates the sensor resistance (Rs)
def MQResistance(readadc, rl_value):
    return ((1024 * 1000 * rl_value) / (readadc - rl_value))
    #Rs = (22000 * (5 - vrl)) / vrl
    #return Rs 

# Calculates the sensor resistance of clean air from the MQ131 sensor
def MQCalibration(rs):
    Ro = rs * math.exp((math.log(pcCurve[0] / 0.010) / pcCurve[1]))
    return Ro 

# Calculates the ratio of Rs and Ro from a sensor
def RsRoRatio(Rs, Ro):
    return (Rs / Ro)

# Calculates the Parts Per Million (ppm) value
def calculatePPM(RsRoRatio, Ro):
    ppm = (pcCurve[0] * math.pow((RsRoRatio / Ro), pcCurve[1]))
    return ppm

# Converts the Parts Per Million (ppm) value to Parts Per Billion (ppb)
def convertPPMToPPB(ppm):
    return ppm * 1000

def main():
    print "03 Sensor Data"
    print "-----------------------------------------------------------------"
    try:
        # Run forever
        count = 0
        while True:
            print "|",
            for adcnum in range(1):
                # Analog to Digital Conversion from the MQ3002 chip to get voltage
                # Get 5 reading to get a stable value 
                o3SensorAnalogValue1 = readadc(adcnum, SPICLK, SPIMOSI, SPIMISO, SPICS)
                print "The Analog to Digital value1 ",
                print  o3SensorAnalogValue1, "\t",
                count += 1
                time.sleep(5) # Every five seconds
                o3SensorAnalogValue2 = readadc(adcnum, SPICLK, SPIMOSI, SPIMISO, SPICS)
                print "The Analog to Digital value2 ",
                print  o3SensorAnalogValue2, "\t",
                count += 1
                time.sleep(5) # Every five seconds
                o3SensorAnalogValue3 = readadc(adcnum, SPICLK, SPIMOSI, SPIMISO, SPICS)
                print "The Analog to Digital value3 ",
                print  o3SensorAnalogValue3, "\t",
                count += 1
                time.sleep(5) # Every five seconds
                o3SensorAnalogValue4 = readadc(adcnum, SPICLK, SPIMOSI, SPIMISO, SPICS)
                print "The Analog to Digital value4 ",
                print  o3SensorAnalogValue4, "\t",
                count += 1
                time.sleep(5) # Every five seconds
                o3SensorAnalogValue5 = readadc(adcnum, SPICLK, SPIMOSI, SPIMISO, SPICS)
                print "The Analog to Digital value5 ",
                print  o3SensorAnalogValue5, "\t",
                count += 1
                
                # Average reading 
                o3SensorAnalogValueAvg = (o3SensorAnalogValue1 + o3SensorAnalogValue2 + o3SensorAnalogValue3 + o3SensorAnalogValue4 + o3SensorAnalogValue5) / count
                print "The Analog to Digital value avg ",
                print  o3SensorAnalogValueAvg, "\t",
                count = 0 # reset counter

                # Voltage from average reading
                voltage = voltageADC(o3SensorAnalogValueAvg)

                # Get vrl for Rs value
                #Vrl = vrl(o3SensorAnalogValueAvg)

                # Get the Rs value from the average of the 5 readings
                Rs = MQResistance(o3SensorAnalogValueAvg, RL_MQ131)

                # Get the Ro value from the average of the 5 readings
                Ro =  MQCalibration(Rs)

                # Get Ratio from the Rs and Ro values
                Rs_Ro_Ratio = RsRoRatio(Rs, Ro)

                # Get the ppm value from the average of the 5 readings
                ppm = calculatePPM(Rs_Ro_Ratio, Ro)

                # Convert the ppm value to ppb value
                ppb = convertPPMToPPB(ppm)

                print "The PPB ",
                print  ppb, "\t",
                
                post_observation(featureOfInterestId="f8ee9ea0-1279-11e7-b571-452d030d47d5",
                    datastreamId="230ba5a0-127c-11e7-b571-452d030d47d5",
                    phenomenonTime=datetime.datetime.now().isoformat(),
                    result=str(ppb),
                    parameters={"voltage": str(voltage), "Rs": str(Rs), "Ro": str(Ro), "Rs_Ro_Ratio": str(Rs_Ro_Ratio)})

            print "|"

    except KeyboardInterrupt:
        GPIO.cleanup()
        

main()


