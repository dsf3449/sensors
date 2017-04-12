import sched
import time
import datetime
import os
import io

import requests
from requests_toolbelt.adapters import host_header_ssl

from sensors.common.logging import configure_logger
from sensors.persistence.sqlite import SqliteRepository


logger = configure_logger()
jwt_token = (None, None)
# Requests session
session = None

# Per-device ID and key.
JWT_ID = os.environ.get('JWT_ID', "2694b9e1-ce59-4fd5-b95e-aa1c780e8158")
JWT_KEY = os.environ.get('JWT_KEY', "ecacdce7-7374-408b-997b-5877bf9e37c3")

TRANSMIT_INTERVAL_SECONDS = 15
SCHEDULE_PRIORITY_DEFAULT = 1
ERROR_RESPONSE = 'error'

AUTH_TTL = datetime.timedelta(minutes=int(os.environ.get('CGIST_AUTH_TTL', "15")))

URL = os.environ.get('CGIST_URL',
                     'https://sensorthings.southcentralus.cloudapp.azure.com/device/api/v1.0/CreateObservations')
URL_AUTH = os.environ.get('CGIST_AUTH_URL',
                          'https://sensorthings.southcentralus.cloudapp.azure.com/device/api/auth/login')
# ONLY SET THIS IN DEVELOPMENT!!!
VERIFY_SSL = not bool(os.environ.get('CGIST_IGNORE_SSL_ERRORS', False))

SUCCESS_STATUS_CODE = 201

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
        r = session.post(URL_AUTH, headers=headers, data=json, verify=VERIFY_SSL)
        print(("Auth status code was {0}".format(r.status_code)))
        if r.status_code != 200:
            print("ERROR: Authentication failed")
            new_token = (None, None)
        else:
            new_token = (r.json()["token"], datetime.datetime.utcnow())

    return new_token


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
                    # There is one or more remaining Datastream(s)
                    json.write(',')
        json.write(']')
    json_str = json.getvalue()
    json.close()

    return json_str


def transmit(repo):
    global jwt_token
    obs = repo.get_observations()
    logger.debug("Transmitter: read {0} observations from DB.".format(len(obs)))
    if len(obs) > 0:
        # Serialize observations to SensorThings dataArray JSON
        obs_dict = observations_list_to_dict(obs)
        json = observations_to_json(obs_dict)
        logger.debug("Transmitter: JSON payload: {0}".format(json))
        # POST observations
        jwt_token = jwt_authenticate(jwt_token)
        if jwt_token[0] is None:
            raise AuthenticationException()

        headers = {'Content-Type': 'application/json',
                   'Authorization': "Bearer {token}".format(token=jwt_token[0])}
        logger.debug("Transmitter: Posting data to {0}...".format(URL))
        r = session.post(URL, headers=headers, data=json, verify=VERIFY_SSL)
        logger.debug("Transmitter: Status code was {0}".format(r.status_code))
        if r.status_code != SUCCESS_STATUS_CODE:
            raise TransmissionException("Transmission failed with status code: {0}".format(r.status_code))

        # Remove observations from local data, unless the observation could not be
        #   created, then update its status to error.
        ids_to_delete = []
        ids_to_update_status = []

        for (i, e) in enumerate(r.json()):
            if e == ERROR_RESPONSE:
                ids_to_update_status.append(obs[i].id)
            else:
                ids_to_delete.append(obs[i].id)

        repo.delete_observations(ids_to_delete)
        logger.debug("Transmitter: Successfully submitted {0} observations.".format(len(ids_to_delete)))
        repo.update_observation_status(ids_to_update_status, status=SqliteRepository.STATUS_ERROR)
        mesg = ("Transmitter: Failed to submit {0} observations, "
                "which were retained in local database with status {1}.").format(len(ids_to_update_status),
                                                                                 SqliteRepository.STATUS_ERROR)
        logger.debug(mesg)


def main():
    repo = SqliteRepository()
    s = sched.scheduler(time.time, time.sleep)

    global session
    session = requests.session()
    if not VERIFY_SSL:
        session.mount('https://', host_header_ssl.HostHeaderSSLAdapter())

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
        except AuthenticationException:
            logger.error("Transmitter: Error authenticating to {0}".format(URL_AUTH))
        except TransmissionException as te:
            logger.error("Transmitter: {0}".format(te.message))
        finally:
            pass
    logger.info("Transmitter: exiting.")


class AuthenticationException(Exception):
    pass


class TransmissionException(Exception):
    def __init__(self, message):
        self.message = message
