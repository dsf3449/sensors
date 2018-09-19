#!/usr/bin/python

"""LearnSensorthingsClient.

Author: Karthik Chepudira
Date Created:** 4/24/2018
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
from pandas.io.json import json_normalize
# import aqi
import uuid

from IPython.core.debugger import set_trace

class LearnSTAClient:

    def __init__(self, baseurl, authurl, authID, authkey,VERIFY_SSL=False):
        self.baseurl = baseurl
        self.authurl = authurl
        self.authID = authID
        self.authkey = authkey
        self.authtoken = None
        self.authtokents = None
        self.VERIFY_SSL = VERIFY_SSL
        
    def jwt_authenticate(self):
        
        JWT_ID=self.authID
        JWT_KEY=self.authkey
        URL_AUTH =self.authurl
        VERIFY_SSL=self.VERIFY_SSL
        AUTH_TTL=datetime.timedelta(minutes=5)
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
                print ("Unable to authenticate to {0} due to error: {1}".format(URL_AUTH, str(e)))
                #raise AuthenticationException("Unable to authenticate to {0} due to error: {1}".format(URL_AUTH, str(e)))
            print (("Transmitter: Auth status code was {0}".format(r.status_code)))
            if r.status_code != 200:
                print ("Authentication failed with status code {0}".format(str(r.status_code)))
                #raise AuthenticationException("Authentication failed with status code {0}".format(str(r.status_code)))
            else:
                new_token = (r.json()["token"], datetime.datetime.utcnow())

        return new_token
         
    def createlocation(self,name,description,latitude,longitude):
        geometry= {}
        geometry['type']= "Point"
        geometry['coordinates']=[float(longitude),float(latitude)]
        location = {}
        location['type']="Feature"
        location['geometry']=geometry
        stalocation={}
        stalocation['name']=name
        stalocation['description']=description
        stalocation['encodingType']="application/vnd.geo+json"
        stalocation['location']=location
        return stalocation

    ## Create Thing
    def createThing(self,locationid,name,description,networkid,deploymenttime):
        location = {}
        location['@iot.id']=locationid.replace("'", "")
        properties={}
        properties['network_id']=networkid
        properties['deployment_time']=deploymenttime
        stathing={}
        stathing['Locations']=[location]
        stathing['name']=name
        stathing['description']=description.replace('"', '')
        stathing['properties']=properties
        print (stathing)
        return stathing

    ## Create FeaturesOfInterest
    def createFeaturesOfInterest(self,name,description,latitude,longitude):
        geometry= {}
        geometry['type']= "Point"
        geometry['coordinates']=[float(longitude),float(latitude)]
        location = {}
        location['type']="Feature"
        location['geometry']=geometry
        stafeature={}
        stafeature['name']=name
        stafeature['description']=description
        stafeature['encodingType']="application/vnd.geo+json"
        stafeature['feature']=location
        #print (stafeature)
        return stafeature

    ## Create Sensor
    def createSensor(self,name,description,metadata):
        stasensor={}
        stasensor['name']=name
        stasensor['description']=description
        stasensor['encodingType']="application/pdf"
        stasensor['metadata']=metadata
        return stasensor

    ## Create DataStream
    def createDatastream(self,thingid,sensorid,observedpropertyid,name,description,
                         measurementunit,measurementsymbol,measurementdefinition
                         ,observationtype):

        thing = {}
        thing["@iot.id"]=thingid.replace("'", "")
        sensor = {}
        sensor["@iot.id"]=sensorid.replace("'", "")
        obproperty = {}
        obproperty["@iot.id"]=observedpropertyid.replace("'", "")
        unitOfMeasurement={}
        unitOfMeasurement["name"]=measurementunit
        unitOfMeasurement["symbol"]=measurementsymbol
        unitOfMeasurement["definition"]=measurementdefinition
        stadatastream={}
        stadatastream["Thing"]=thing
        stadatastream["Sensor"]=sensor
        stadatastream["ObservedProperty"]=obproperty
        stadatastream["name"]=name
        stadatastream["description"]=description
        stadatastream["unitOfMeasurement"]=unitOfMeasurement
        stadatastream["observationType"]=observationtype
        print (stadatastream)
        return stadatastream

    def createsensor(self,name,description,encodingtype,metadata):
        session = requests.session()
        sensor={}
        sensor['name']=name
        sensor['encodingType']=encodingtype
        sensor['description']=description
        sensor['metadata']=metadata
        sensorjson=json.dumps(sensor, ensure_ascii=False).encode('utf8')
        jwt_token = self.jwt_authenticate()
        print (sensorjson)
        headers = {'Content-Type': 'application/json','Authorization': "Bearer {token}".format(token=jwt_token[0])}
        r = session.post(self.baseurl+"/Sensors", headers=headers, data=sensorjson, verify=self.VERIFY_SSL)
        print (r)
    
    def createobservedproperty(self,name,definition,description):
        session = requests.session()
        obsprop={}
        obsprop['name']=name
        obsprop['definition']=definition
        obsprop['description']=description
        obspropjson=json.dumps(obsprop, ensure_ascii=False).encode('utf8')
        jwt_token = self.jwt_authenticate()
        headers = {'Content-Type': 'application/json','Authorization': "Bearer {token}".format(token=jwt_token[0])}
        r = session.post(self.baseurl+"/ObservedProperties", headers=headers, data=obspropjson, verify=self.VERIFY_SSL)
        print (r)
    
    def createlocationrec(self,name,description,latitude,longitude):
        session = requests.session()
        obsloc=self.createlocation(name,description,latitude,longitude)
        obslocjson=json.dumps(obsloc, ensure_ascii=False).encode('utf8')
        jwt_token = self.jwt_authenticate()
        headers = {'Content-Type': 'application/json','Authorization': "Bearer {token}".format(token=jwt_token[0])}
        r = session.post(self.baseurl+"/Locations", headers=headers, data=obslocjson, verify=self.VERIFY_SSL)
        print (r)
    
    def createsensorthing(self,row):
        session = requests.session()
        try:
            # Get Token
            jwt_token = self.jwt_authenticate()
            print (jwt_token)
            headers = {'Content-Type': 'application/json','Authorization': "Bearer {token}".format(token=jwt_token[0])}

            # Create Thing
            print ("Creating Things")
            thingjson =json.dumps(self.createThing(row['locationid'],row['thname'],row['thdesc'],row['thnetid'],
                                                   row['thdeploytime']), ensure_ascii=False).encode('utf8')
            r = session.post(self.baseurl+"/Things", headers=headers, data=thingjson, verify=self.VERIFY_SSL)
            print (" Printing thing headers ")
            print (r.headers)
            thstr=r.headers["Location"]
            thingid=thstr[thstr.find("(")+1:thstr.find(")")]
            #print (thstr)
            #print (thingid)
            return thingid
        except:
            raise
            print ("error")
            return 'Error'
        
    def createdatastream(self,row):
        session = requests.session()
        try:
            # Get Token
            jwt_token = self.jwt_authenticate()
            print (jwt_token)
            headers = {'Content-Type': 'application/json; charset=utf-8','Authorization': "Bearer {token}".format(token=jwt_token[0])}

            # Create Datastream
            print ("Creating Datastreams")
#             set_trace()
            dsjson =json.dumps(self.createDatastream(row['stathingid'],row['dssensorid'],row['dsobspropertyid'],row['dsname'],
                                                     row['dsdesc'],row['dsmunit'],row['dsmsymbol'],
                                                     row['dsmdefinition'],row['dsobstype']), ensure_ascii=False).encode('utf8')
            r = session.post(self.baseurl+"/Datastreams", headers=headers, data=dsjson, verify=self.VERIFY_SSL)
            dsstr=r.headers["Location"]
            dsstrid=dsstr[dsstr.find("(")+1:dsstr.find(")")]
            print (dsstr,dsstrid)
            return dsstrid

        except:
            return 'Error'

    def createdatastreamQAQC(self,row):
        session = requests.session()
        if row['sensortype']!='mq131':
            return ''
#         try:
            # Get Token
        jwt_token = self.jwt_authenticate()
        print (jwt_token)
        headers = {'Content-Type': 'application/json','Authorization': "Bearer {token}".format(token=jwt_token[0])}

        # Create Datastream
        print ("Creating Datastreams QAQC")
        dsjson =json.dumps(self.createDatastream(row['stathingid'],row['dssensorid'],row['dsobspropertyid'],row['QAQC_dsname'],
                                                 row['dsdesc'],row['dsmunit'],row['dsmsymbol'],
                                                 row['dsmdefinition'],row['dsobstype']), ensure_ascii=False)
        r = session.post(self.baseurl+"/Datastreams", headers=headers, data=dsjson, verify=self.VERIFY_SSL)
        dsstr=r.headers["Location"]
        dsstrid=dsstr[dsstr.find("(")+1:dsstr.find(")")]
        print (dsstr,dsstrid)
        return dsstrid
#        return ""

#         except:
#             return 'Error'
    
    def createdatastreamAQI(self,row):
        session = requests.session()
        if row['sensortype']!='mq131':
            return ''
#         try:
            # Get Token
        jwt_token = self.jwt_authenticate()
        print (jwt_token)
        headers = {'Content-Type': 'application/json','Authorization': "Bearer {token}".format(token=jwt_token[0])}

        # Create Datastream
        print ("Creating Datastreams AQI")
        dsjson =json.dumps(self.createDatastream(row['stathingid'],row['dssensorid'],row['AQI_dsobspropertyid'],row['AQI_dsname'],
                                                 row['AQI_dsdesc'],row['AQI_dsmunit'],row['AQI_dsmsymbol'],
                                                 row['AQI_dsmdefinition'],row['AQI_dsobstype']), ensure_ascii=False)
        r = session.post(self.baseurl+"/Datastreams", headers=headers, data=dsjson, verify=self.VERIFY_SSL)
        dsstr=r.headers["Location"]
        dsstrid=dsstr[dsstr.find("(")+1:dsstr.find(")")]
        print (dsstr,dsstrid)
        return dsstrid
#        return ""

#         except:
#             return 'Error'
        
    def Getuuid(self,row):
        return uuid.uuid4()
        
    def createthings(self,inputthingsfilepath,outputthingsfilepath):
        dfthings=pd.read_csv(inputthingsfilepath)
        dfthings['stathingid'] =dfthings.apply(self.createsensorthing, axis=1)
        dfthings['jwt_id'] = dfthings.apply(self.Getuuid, axis=1)
        dfthings['jwt_key'] = dfthings.apply(self.Getuuid, axis=1)
#         dfthings['stalocationid'] = dfthings.apply(self.Getuuid, axis=1)
        dfthings.to_csv(outputthingsfilepath,index=False)
        
    def createdatastreams(self,inputdatastreamsfilepath,outputdatastreamsfilepath,inputthingsfilepath):
        dfthings=pd.read_csv(inputthingsfilepath)
        dfdatastreams=pd.read_csv(inputdatastreamsfilepath)
        dfdatastreams=dfdatastreams.merge(dfthings,on='devicenum', how='left')
        dfdatastreams['stadatastreamid'] =dfdatastreams.apply(self.createdatastream, axis=1)
        dfdatastreams['QAQC_stadatastreamid'] =dfdatastreams.apply(self.createdatastreamQAQC, axis=1)
        dfdatastreams['AQI_stadatastreamid'] =dfdatastreams.apply(self.createdatastreamAQI, axis=1)
        dfdatastreams.to_csv(outputdatastreamsfilepath,index=False)
    
    # custom function to add the QAQC, AQI datastreams.
    def patchdatastreams(self,inputdatastreamsfilepath,outputdatastreamsfilepath,inputthingsfilepath):
        #dfthings=pd.read_csv(inputthingsfilepath)
        dfdatastreams=pd.read_csv(inputdatastreamsfilepath,encoding = "cp1252").head(1)   
        dfdatastreams["AQI_dsmsymbol"]="ppm"
        #dfdatastreams=dfdatastreams.merge(dfthings,on='devicenum', how='left')
        dfdatastreams['QAQC_stadatastreamid'] =dfdatastreams.apply(self.createdatastreamQAQC, axis=1)
        dfdatastreams['AQI_stadatastreamid'] =dfdatastreams.apply(self.createdatastreamAQI, axis=1)
        dfdatastreams.to_csv(outputdatastreamsfilepath,index=False)   
    
    def createagentssql(self, inputthingsfilepath, agentsfilepath):
        dfthings=pd.read_csv(inputthingsfilepath)
        filepath = agentsfilepath + "/agents-append-" + now.isoformat() + ".sql"
        with open(filepath, 'w') as cfile:
            for idx, row in dfthings.iterrows():
                cfile.write("--Small thing {0}\n".format(idx))
                cfile.write("insert into agents(id, key) values ('{jwt_id}', '{jwt_key}');\n".format(jwt_id=row['jwt_id'],
                                                                                                     jwt_key=row['jwt_key']))
                
    def createthingsyml(self,inputthingsfilepath,inputdatastreamsfilepath,ymlfilepath):
        dfthings=pd.read_csv(inputthingsfilepath)
        dfdatastreams=pd.read_csv(inputdatastreamsfilepath)
        dfsta=dfdatastreams.merge(dfthings,on='devicenum', how='left')
        devices = list(dfsta['devicenum'].unique())
        for devicenum in devices:
            filepath = ymlfilepath+"/"+str(devicenum)+".yml"
            with open(filepath, 'w') as cfile:
                #stathingid=str(dfdevice[dfdevice['devicenum']==devnum].iloc[0]['stathingid'])
                stathingid=str(dfthings[dfthings['devicenum']==devicenum].iloc[0]['stathingid'])
                locationid=str(dfthings[dfthings['devicenum']==devicenum].iloc[0]['locationid'])
                jwt_key=str(dfthings[dfthings['devicenum']==devicenum].iloc[0]['jwt_key'])
                jwt_id=str(dfthings[dfthings['devicenum']==devicenum].iloc[0]['jwt_id'])
                stadatastreamslist=list(dfdatastreams[dfdatastreams['devicenum']==devicenum]['stadatastreamid'].unique())
                stasensortypeslist=list(dfdatastreams[dfdatastreams['devicenum']==devicenum]['sensortype'].unique())
                cfile.write("logging:"+'\n')
                cfile.write("  logger_path: /var/log/sensor.log"+'\n')
                cfile.write("  level_file: WARNING"+'\n')
                cfile.write("  level_console: WARNING"+'\n')
                cfile.write("spooler:"+'\n')
                cfile.write("  db_path: /var/spool/sensor.sqlite"+'\n')
                cfile.write("thing:"+'\n')
                cfile.write("  id: "+stathingid.replace("'", "")+'\n')
                cfile.write("  location_id: "+locationid.replace("'", "")+'\n')
                cfile.write("sensors:"+'\n')
                # loop through sensortypes
                for stype in stasensortypeslist:
                    stasensorlist=list(dfdatastreams[(dfdatastreams['devicenum']==devicenum) & (dfdatastreams['sensortype']==stype)]['sensorname'].unique())
                    cfile.write("  - type: "+stype+'\n')
                    cfile.write("    observed_properties:"+'\n')
                    for sname in stasensorlist:
                     # loop through observed properties
                        cfile.write("      - name: "+sname+'\n')
                        stadsid=list(dfdatastreams[(dfdatastreams['devicenum']==devicenum) & (dfdatastreams['sensortype']==stype) & (dfdatastreams['sensorname']==sname)]['stadatastreamid'].unique())
                        cfile.write("        datastream_id: "+stadsid[0].replace("'", "")+'\n')                    
                cfile.write("transports:"+'\n')
                cfile.write("  - type: https"+'\n')
                cfile.write("    properties:"+'\n')
                cfile.write("      auth_url: https://test1-sta-api.learnlafayette.com/SensorThingsService/auth/login"+'\n')
                cfile.write("      url: https://test1-sta-api.learnlafayette.com/SensorThingsService/v1.0/"+'\n')
                cfile.write("      jwt_id: "+jwt_id+'\n')
                cfile.write("      jwt_key: "+jwt_key+'\n')
                cfile.write("      jwt_token_ttl_minutes: 15"+'\n')
                cfile.write("      transmit_interval_seconds: 15"+'\n')
                cfile.write("      verify_ssl: true"+'\n')