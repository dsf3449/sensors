import sched
import time
import datetime
import os
import io

import requests

from sensors.common.logging import configure_logger
from sensors.persistence.sqlite import SqliteRepository


logger = configure_logger()

# Per-device ID and key.
JWT_ID = os.environ.get('JWT_ID', "2694b9e1-ce59-4fd5-b95e-aa1c780e8158")
JWT_KEY = os.environ.get('JWT_KEY', "ecacdce7-7374-408b-997b-5877bf9e37c3")

# Feature of Interest ID and Datastream ID
# FOI_ID = os.environ['FEATURE_OF_INTEREST_ID']
# DS_ID = os.environ['DATASTREAM_ID']

TRANSMIT_INTERVAL_SECONDS = 15
SCHEDULE_PRIORITY_DEFAULT = 1

AUTH_TTL = datetime.timedelta(minutes=15)

# SensorThings API in Microsoft Azure instance with authentication
URL = "https://sensorthings.southcentralus.cloudapp.azure.com/device/api/v1.0/Observations"
URL_AUTH = "https://sensorthings.southcentralus.cloudapp.azure.com/device/api/auth/login"

# SensorThings API in Microsoft Azure instance withont authentication
# URL = "http://sensorthings.southcentralus.cloudapp.azure.com:8080/device/api/v1.0/Observations"

# JSON id / values to send to SensorThings API standard
# JSON_TEMPLATE = '''{{"FeatureOfInterest":{{"@iot.id":"{featureOfInterestId}"}},
#   "Datastream":{{"@iot.id":"{datastreamId}"}},
#   "phenomenonTime":"{phenomenonTime}",
#   "parameters":{{{parametersStr}}},
#   "result":"{result}"
# }}'''

# JWT authentication request token
AUTH_TEMPLATE = '''{{"id":"{id}","key":"{key}"}}'''

# JSON template for a single SensorThings Datastream within a dataArray POST request
JSON_DATASTREAM = ('{{"Datastream":{{"@iot.id":"{datastreamId}"}},'
                   '"components":["phenomenonTime","result","FeatureOfInterest/id","parameters"],'
                   '"dataArray@iot.count":{count},'
                   '"dataArray":[{dataArray}]'
                   '}}')

JSON_DATA_ARRAY_ELEM = ('['
                        '"{phenomenonTime}",'
                        '"{result}",'
                        '"{featureOfInterestId}",'
                        '{{{parameters}}}'
                        ']')

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
# def post_observation(token,
#                      featureOfInterestId,
#                      datastreamId,
#                      phenomenonTime,
#                      result,
#                      parameters={}):
#     parametersStr = ",".join(['"{k}":"{v}"'.format(k=e[0], v=e[1]) for e in list(parameters.items())])
#     json = JSON_TEMPLATE.format(featureOfInterestId=featureOfInterestId,
#                                 datastreamId=datastreamId,
#                                 phenomenonTime=phenomenonTime,
#                                 result=result,
#                                 parametersStr=parametersStr)
#     print(("Posting new data {0}".format(json)))
#     headers = {'Content-Type': 'application/json',
#                'Authorization': "Bearer {token}".format(token=token[0])}
#     r = requests.post(URL, headers=headers, data=json)
#     print(("Status code was {0}".format(r.status_code)))
#     location = r.headers['Location']
#     print(("Location: {0}".format(location)))

def observations_list_to_dict(observations):
    d = {}
    for o in observations:
        obs_for_datastream = d.get(o.datastreamId, [])
        obs_for_datastream.append(o)
        d[o.datastreamId] = obs_for_datastream
    return d


def observations_to_json(observations_dict):
    json = io.StringIO()

    datastreams = observations_dict.keys()
    numDatastreams = len(datastreams)

    if numDatastreams > 0:
        json.write('[')
        for (i, datastreamId) in enumerate(datastreams, start=1):
            obs_for_ds = observations_dict[datastreamId]
            count = len(obs_for_ds)
            if count > 0:
                # First, generate observation dataArray
                dataArray = io.StringIO()
                # Write first element to dataArray
                o = obs_for_ds[0]
                e = JSON_DATA_ARRAY_ELEM.format(phenomenonTime=o.phenomenonTime,
                                                result=o.result,
                                                featureOfInterestId=o.featureOfInterestId,
                                                parameters=o.get_parameters_as_str())
                dataArray.write(e)
                # Write remaining elements to dataArray
                for o in obs_for_ds[1:]:
                    e = JSON_DATA_ARRAY_ELEM.format(phenomenonTime=o.phenomenonTime,
                                                    result=o.result,
                                                    featureOfInterestId=o.featureOfInterestId,
                                                    parameters=o.get_parameters_as_str())
                    dataArray.write(',')
                    dataArray.write(e)
                # Second, generate Datastream JSON (with all dataArray elements)
                d = JSON_DATASTREAM.format(datastreamId=datastreamId,
                                           count=count,
                                           dataArray=dataArray.getvalue())
                dataArray.close()
                # Third, write Datastream JSON
                json.write(d)
                if i < numDatastreams:
                    # There is following Datastream
                    json.write(',')
        json.write(']')
    json_str = json.getvalue()
    json.close()

    return json_str


def transmit(repo):
    obs = repo.get_observations()
    logger.debug("Transmitter: read {0} observations from DB.".format(len(obs)))
    if len(obs) > 0:
        obs_dict = observations_list_to_dict(obs)
        json = observations_to_json(obs_dict)
        logger.debug("Transmitter: JSON payload: {0}".format(json))


def main():
    repo = SqliteRepository()
    s = sched.scheduler(time.time, time.sleep)

    while True:
        try:
            logger.debug("Transmitter: scheduling network transmission...")
            s.enter(TRANSMIT_INTERVAL_SECONDS,
                    SCHEDULE_PRIORITY_DEFAULT,
                    transmit,
                    argument=(repo,))
            logger.debug("Transmitter: Running scheduler...")
            s.run()
            logger.debug("Transmitter: End of iteration.")
        except KeyboardInterrupt:
            break
        finally:
            pass
    logger.info("Transmitter: exiting.")
