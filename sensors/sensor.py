#!/usr/bin/env python

###  CGI Digital Services - LEaRN 
###  March 2017
###  Application to read O3 Senser (MQ315) from the Raspberry Pi 3 Rev. B 
###  Converts the analog value to digital value with the MCP3002 chip
###  Once we have that value, it will convert it to an equation to get the parts per billion (ppb) value
###  Finally, the value will be stored in a JSON object to POST a request from the SensorThings API that is in an Microsoft Azure instance
###  V0.0.1

import os
import glob
import datetime
import time
import json
import math
import requests

import RPi.GPIO as GPIO

# Only for testing to demonstrate re-authentication
import time

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

# Per-device ID and key.
JWT_ID = os.environ['JWT_ID']
JWT_KEY = os.environ['JWT_KEY']

# Feature of Interest ID and Datastream ID 
FOI_ID = os.environ['FEATURE_OF_INTEREST_ID']
DS_ID = os.environ['DATASTREAM_ID']
 
AUTH_TTL = datetime.timedelta(minutes=15)

# SensorThings API in Microsoft Azure instance with authentication 
URL = "https://sensorthings.southcentralus.cloudapp.azure.com/device/api/v1.0/Observations"
URL_AUTH = "https://sensorthings.southcentralus.cloudapp.azure.com/device/api/auth/login"

# SensorThings API in Microsoft Azure instance withont authentication
# URL = "http://sensorthings.southcentralus.cloudapp.azure.com:8080/device/api/v1.0/Observations"

# JSON id / values to send to SensorThings API standard
JSON_TEMPLATE = '''{{"FeatureOfInterest":{{"@iot.id":"{featureOfInterestId}"}},
  "Datastream":{{"@iot.id":"{datastreamId}"}},
  "phenomenonTime":"{phenomenonTime}",
  "parameters":{{{parametersStr}}},
  "result":"{result}"
}}'''

# JWT anthenication standard 
AUTH_TEMPLATE = '''{{"id":"{id}","key":"{key}"}}'''

# Method to authenticate using JSON Web Token (JWT)
# and check if you need it or not
def jwt_authenticate(token=(None, None)):
    new_token = token
    auth_required = False
 
    # Figure out if authentication is required, that is: (1) if we have never authenticated (token_timestamp is None);
    #   or (2) token_timestamp is later than or equal to the current time + AUTH_TTL
    token_timestamp = token[1]
    if token_timestamp is None:
        print("Auth token is null, authenticating ...")
        auth_required = True
    else:
        token_expired_after = token_timestamp + AUTH_TTL
        if datetime.datetime.utcnow() >= token_expired_after:
            print("Auth token expired, re-authenticating ...")
            auth_required = True
 
    if auth_required:
        json = AUTH_TEMPLATE.format(id=JWT_ID, key=JWT_KEY)
        headers = {'Content-Type': 'application/json'}
        r = requests.post(URL_AUTH, headers=headers, data=json)
        print(("Auth status code was {0}".format(r.status_code)))
        if r.status_code != 200:
            print("ERROR: Authentication failed")
            new_token = (None, None)
        else:
            new_token = (r.json()["token"], datetime.datetime.utcnow())
 
    return new_token

# POST to SensorThings API after average ppb is calculated
def post_observation(token,
                     featureOfInterestId,
                     datastreamId,
                     phenomenonTime,
                     result,
                     parameters={}):
    parametersStr = ",".join(['"{k}":"{v}"'.format(k=e[0], v=e[1]) for e in list(parameters.items())])
    json = JSON_TEMPLATE.format(featureOfInterestId=featureOfInterestId,
                                datastreamId=datastreamId,
                                phenomenonTime=phenomenonTime,
                                result=result,
                                parametersStr=parametersStr)
    print(("Posting new data {0}".format(json)))
    headers = {'Content-Type': 'application/json',
               'Authorization': "Bearer {token}".format(token=token[0])}
    r = requests.post(URL, headers=headers, data=json)
    print(("Status code was {0}".format(r.status_code)))
    location = r.headers['Location']
    print(("Location: {0}".format(location)))

# Example showing first-time authentication
def first_time_auth(jwt_token, ppb, voltage, Rs, Ro, Rs_Ro_Ratio):
    jwt_token = jwt_authenticate(jwt_token)
    if jwt_token[0] is None:
        print("Unable to authenticate using JWT")
    else:
        post_observation(token=jwt_token,
                         featureOfInterestId=FOI_ID,
                         datastreamId=DS_ID,
                         phenomenonTime=datetime.datetime.now().isoformat(),
                         result=str(ppb),
                         parameters={"voltage": str(voltage), "Rs": str(Rs), "Ro": str(Ro), "Rs_Ro_Ratio": str(Rs_Ro_Ratio)})

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
    # Initializes the token 
    jwt_token = (None, None)

    print("O3 Sainsmart Sensor Data")
    print("-----------------------------------------------------------------")
    try:
        # Run forever
        count = 0
        while True:
            print("|", end=' ')
            for adcnum in range(1):
                # Analog to Digital Conversion from the MQ3002 chip to get voltage
                # Get 5 reading to get a stable value 
                o3SensorAnalogValue1 = readadc(adcnum, SPICLK, SPIMOSI, SPIMISO, SPICS)
                #print "The Analog to Digital value1 ",
                #print  o3SensorAnalogValue1, "\t",
                count += 1
                time.sleep(5) # Every five seconds
                o3SensorAnalogValue2 = readadc(adcnum, SPICLK, SPIMOSI, SPIMISO, SPICS)
                #print "The Analog to Digital value2 ",
                #print  o3SensorAnalogValue2, "\t",
                count += 1
                time.sleep(5) # Every five seconds
                o3SensorAnalogValue3 = readadc(adcnum, SPICLK, SPIMOSI, SPIMISO, SPICS)
                #print "The Analog to Digital value3 ",
                #print  o3SensorAnalogValue3, "\t",
                count += 1
                time.sleep(5) # Every five seconds
                o3SensorAnalogValue4 = readadc(adcnum, SPICLK, SPIMOSI, SPIMISO, SPICS)
                #print "The Analog to Digital value4 ",
                #print  o3SensorAnalogValue4, "\t",
                count += 1
                time.sleep(5) # Every five seconds
                o3SensorAnalogValue5 = readadc(adcnum, SPICLK, SPIMOSI, SPIMISO, SPICS)
                #print "The Analog to Digital value5 ",
                #print  o3SensorAnalogValue5, "\t",
                count += 1
                
                # Average reading 
                o3SensorAnalogValueAvg = (o3SensorAnalogValue1 + o3SensorAnalogValue2 + o3SensorAnalogValue3 + o3SensorAnalogValue4 + o3SensorAnalogValue5) / count
                print("The Analog to Digital value avg ", end=' ')
                print(o3SensorAnalogValueAvg, "\t", end=' ')
                count = 0 # reset counter

                # Voltage from average reading
                voltage = voltageADC(o3SensorAnalogValueAvg)

                # Get the Rs value (O3 concentrations of gases) from the average of the 5 readings
                Rs = MQResistance(o3SensorAnalogValueAvg, RL_MQ131)

                # Get the Ro (Clean Air) value from the average of the 5 readings
                Ro =  MQCalibration(Rs)

                # Get Ratio from the Rs and Ro values
                Rs_Ro_Ratio = RsRoRatio(Rs, Ro)

                # Get the ppm value from the average of the 5 readings
                ppm = calculatePPM(Rs_Ro_Ratio, Ro)

                # Convert the ppm value to ppb value
                ppb = convertPPMToPPB(ppm)

                print("The PPB ", end=' ')
                print(ppb, "\t", end=' ')

                # Authentication and POST to SensorThings API
                first_time_auth(jwt_token, ppb, voltage, Rs, Ro, Rs_Ro_Ratio)

            print("|")

    except KeyboardInterrupt:
        GPIO.cleanup()
        
if __name__ == '__main__':
    main()


