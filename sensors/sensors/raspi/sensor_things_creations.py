#!/usr/bin/python

"""LearnSensorthingsClient.

Author: Karthik Chepudira
Date Created:** 6/5/2017
Python version:** 3.6

This is a client library for communicating with a sensorthings api compliant server as per
https://github.com/opengeospatial/sensorthings

"""

import requests
import pandas as pd
import warnings
import json
import time
import sys
import datetime
import json
import random


class LearnSensorthingsClient:
    def __init__(self, baseurl, authurl, authID, authkey, VERIFY_SSL=False):
        self.baseurl = baseurl
        self.authurl = authurl
        self.authID = authID
        self.authkey = authkey
        self.authtoken = None
        self.authtokents = None
        self.VERIFY_SSL = VERIFY_SSL

    def jwt_authenticate(self):

        JWT_ID = self.authID
        JWT_KEY = self.authkey
        URL_AUTH = self.authurl
        VERIFY_SSL = self.VERIFY_SSL
        AUTH_TTL = datetime.timedelta(minutes=5)
        AUTH_TEMPLATE = '''{{"id":"{id}","key":"{key}"}}'''
        token = (self.authtoken, self.authtokents)
        session = requests.session()

        new_token = token
        auth_required = False

        # Figure out if authentication is required, that is: (1) if we have never authenticated (token_timestamp is None);
        #   or (2) token_timestamp is later than or equal to the current time + AUTH_TTL
        token_timestamp = token[1]
        if token_timestamp is None:
            print ("Transmitter: Auth token is null, authenticating ...")
            auth_required = True
        else:
            token_expired_after = token_timestamp + AUTH_TTL
            if datetime.datetime.utcnow() >= token_expired_after:
                print ("Transmitter: Auth token expired, re-authenticating ...")
                auth_required = True

        if auth_required:
            json = AUTH_TEMPLATE.format(id=JWT_ID, key=JWT_KEY)
            headers = {'Content-Type': 'application/json'}
            try:
                r = session.post(URL_AUTH, headers=headers, data=json, verify=VERIFY_SSL)
            except ConnectionError as e:
                raise AuthenticationException(
                    "Unable to authenticate to {0} due to error: {1}".format(URL_AUTH, str(e)))
            print (("Transmitter: Auth status code was {0}".format(r.status_code)))
            if r.status_code != 200:
                raise AuthenticationException("Authentication failed with status code {0}".format(str(r.status_code)))
            else:
                new_token = (r.json()["token"], datetime.datetime.utcnow())

        return new_token

    def getThings(self):
        url = self.baseurl + "/Things"
        response = requests.get(url, verify=self.VERIFY_SSL)
        return response.json()

    def getbias(self, value):
        return 1.05 * value

    def getSensorData(self, datastreamid, targetdatastreamid, featureofinterestid=None):
        url = self.baseurl + "/Datastreams(" + datastreamid + ")/Observations"
        response = requests.get(url, verify=self.VERIFY_SSL)  # To workaround ssl error
        # print url
        try:
            # assumes that recordset sorted by data descending
            robject = requests.get(url, verify=False).json()['value'][0]
            # When ported to the sensor this code will need to be changed to read from the local sqllite.

            JSON_DATASTREAM = ('[{{"Datastream":{{"@iot.id":"{datastreamId}"}},'
                               '"components":["phenomenonTime","result","parameters"],'
                               '"dataArray@iot.count":{count},'
                               '"dataArray":[{dataArray}]'
                               '}}]')

            params = {}
            for item in robject["parameters"]:
                for k in item:
                    # print k, item[k]
                    params[str(k).replace("\'", '"')] = str(item[k]).replace("\'", '"')
            # print params
            darray = [str(robject["phenomenonTime"]).replace("\'", '"'),
                      self.getbias(robject["result"]), params
                      ]

            payload = JSON_DATASTREAM.format(datastreamId=targetdatastreamid,
                                             count=1,
                                             dataArray=json.dumps(darray)
                                             )
            ctime = robject["phenomenonTime"]
            return ctime, payload  # ,topic
        except:
            return None, None  # ,None

    def createlocation(self, name, description, latitude, longitude):
        geometry = {}
        geometry['type'] = "Point"
        geometry['coordinates'] = [float(longitude), float(latitude)]
        location = {}
        location['type'] = "Feature"
        location['geometry'] = geometry
        stalocation = {}
        stalocation['name'] = name
        stalocation['description'] = description
        stalocation['encodingType'] = "application/vnd.geo+json"
        stalocation['location'] = location
        return stalocation

    ## Create Thing
    def createThing(self, locationid, name, description, networkid, deploymenttime):
        location = {}
        location['@iot.id'] = locationid
        properties = {}
        properties['network_id'] = networkid
        properties['deployment_time'] = deploymenttime
        stathing = {}
        stathing['location'] = location
        stathing['name'] = name
        stathing['description'] = description
        stathing['properties'] = properties
        return stathing

    ## Create FeaturesOfInterest
    def createFeaturesOfInterest(self, name, description, latitude, longitude):
        geometry = {}
        geometry['type'] = "Point"
        geometry['coordinates'] = [float(longitude), float(latitude)]
        location = {}
        location['type'] = "Feature"
        location['geometry'] = geometry
        stafeature = {}
        stafeature['name'] = name
        stafeature['description'] = description
        stafeature['encodingType'] = "application/vnd.geo+json"
        stafeature['feature'] = location
        # print (stafeature)
        return stafeature

    ## Create Sensor
    def createSensor(self, name, description, metadata):
        stasensor = {}
        stasensor['name'] = name
        stasensor['description'] = description
        stasensor['encodingType'] = "application/pdf"
        stasensor['metadata'] = metadata
        return stasensor

    ## Create DataStream
    def createDatastream(self, thingid, sensorid, observedpropertyid, name, description,
                         measurementunit, measurementsymbol, measurementdefinition
                         , observationtype):

        thing = {}
        thing['@iot.id'] = thingid
        sensor = {}
        sensor['@iot.id'] = sensorid
        obproperty = {}
        obproperty['@iot.id'] = observedpropertyid
        unitOfMeasurement = {}
        unitOfMeasurement['name'] = measurementunit
        unitOfMeasurement['symbol'] = measurementsymbol
        unitOfMeasurement['definition'] = measurementdefinition
        stadatastream = {}
        stadatastream['Thing'] = thing
        stadatastream['Sensor'] = sensor
        stadatastream['ObservedProperty'] = obproperty
        stadatastream['name'] = name
        stadatastream['description'] = description
        stadatastream['unitOfMeasurement'] = unitOfMeasurement
        stadatastream['observationType'] = observationtype
        #         stadatastream['phenomenonTime']="2017-07-28T01:00:00.000Z/2017-03-23T01:00:00.000Z"
        #         stadatastream['observedArea']={
        #         "type": "Polygon",
        #         "coordinates": [
        #           [
        #             [
        #               -92.042039,
        #               30.221303
        #             ],
        #             [
        #               -92.042239,
        #               30.221303
        #             ],
        #             [
        #               -92.042239,
        #               30.221103
        #             ],
        #             [
        #               -92.042039,
        #               30.221103
        #             ],
        #             [
        #               -92.042039,
        #               30.221303
        #             ]
        #           ]
        #         ]
        #         }
        return stadatastream

    def createsensor(self, name, description, encodingtype, metadata):
        session = requests.session()
        sensor = {}
        sensor['name'] = name
        sensor['encodingType'] = encodingtype
        sensor['description'] = description
        sensor['metadata'] = metadata
        sensorjson = json.dumps(sensor, ensure_ascii=False)
        jwt_token = self.jwt_authenticate()
        print (sensorjson)
        headers = {'Content-Type': 'application/json', 'Authorization': "Bearer {token}".format(token=jwt_token[0])}
        r = session.post(self.baseurl + "/Sensors", headers=headers, data=sensorjson, verify=self.VERIFY_SSL)
        print (r)

    def createobservedproperty(self, name, definition, description):
        session = requests.session()
        obsprop = {}
        obsprop['name'] = name
        obsprop['definition'] = definition
        obsprop['description'] = description
        obspropjson = json.dumps(obsprop, ensure_ascii=False)
        jwt_token = self.jwt_authenticate()
        headers = {'Content-Type': 'application/json', 'Authorization': "Bearer {token}".format(token=jwt_token[0])}
        r = session.post(self.baseurl + "/ObservedProperties", headers=headers, data=obspropjson,
                         verify=self.VERIFY_SSL)
        print (r)

    def createsensorthings(self, row):
        session = requests.session()
        try:
            # Get Token
            jwt_token = self.jwt_authenticate()
            print (jwt_token)
            headers = {'Content-Type': 'application/json', 'Authorization': "Bearer {token}".format(token=jwt_token[0])}

            # Create Location
            print ("Creating Locations")
            locationjson = json.dumps(self.createlocation(row['locname'], row['locdesc'], row['latitude'],
                                                          row['longitude']), ensure_ascii=False)
            r = session.post(self.baseurl + "/Locations", headers=headers, data=locationjson, verify=self.VERIFY_SSL)
            locstr = r.headers["Location"]
            locationid = locstr[locstr.find("(") + 1:locstr.find(")")]

            # Create FeaturesOfInterest
            print ("Creating FeaturesOfInterest")
            featuresjson = json.dumps(self.createFeaturesOfInterest(row['locname'], row['locdesc'], row['latitude'],
                                                                    row['longitude']), ensure_ascii=False)
            r = session.post(self.baseurl + "/FeaturesOfInterest", headers=headers, data=featuresjson,
                             verify=self.VERIFY_SSL)
            # print (r.status_code)
            # locstr=r.headers["Location"]
            # locationid=locstr[locstr.find("(")+1:locstr.find(")")]

            # Create Thing
            print ("Creating Things")
            thingjson = json.dumps(self.createThing(locationid, row['thname'], row['thdesc'], row['thnetid'],
                                                    row['thdeploytime']), ensure_ascii=False)
            r = session.post(self.baseurl + "/Things", headers=headers, data=thingjson, verify=self.VERIFY_SSL)
            thstr = r.headers["Location"]
            thingid = thstr[thstr.find("(") + 1:thstr.find(")")]
            # print (thingid)

            # Create Datastream
            print ("Creating Datastreams")
            dsjson = json.dumps(self.createDatastream(thingid, row['dssensorid'], row['dsobspropertyid'], row['dsname'],
                                                      row['dsdesc'], row['dsmunit'], row['dsmsymbol'],
                                                      row['dsmdefinition'], row['dsobstype']), ensure_ascii=False)
            r = session.post(self.baseurl + "/Datastreams", headers=headers, data=dsjson, verify=self.VERIFY_SSL)
            dsstr = r.headers["Location"]
            return thingid
        except:
            return 'Error'

    def deploy(self, sourcefilepath, destfilepath):
        dfdevice = pd.read_csv(sourcefilepath)
        dfdevice['stathingid'] = dfdevice.apply(self.createsensorthings, axis=1)
        dfdevice.to_csv(destfilepath, index=False)