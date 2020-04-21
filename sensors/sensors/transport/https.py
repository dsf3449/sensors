from datetime import datetime, timedelta

import requests
from requests_toolbelt.adapters import host_header_ssl
from requests.exceptions import ConnectionError

from sensors.domain.transport import Transport
from sensors.common.constants import *
from sensors.config import get_config_element
from sensors.transport import *
from sensors.persistence.sqlite import SqliteRepository


class HttpsTransport(Transport):
    """SensorThings API HTTPS transport with JWT authentication

    """
    DEFAULT_JWT_TTL = '15'
    DEFAULT_TRANSMIT_INTERVAL_SECONDS = '15'
    DEFAULT_VERIFY_SSL = 'true'
    STA_POST_PATH = '/CreateObservations'

    SUCCESS_STATUS_CODE = 201
    ERROR_RESPONSE = 'error'

    # JWT authentication request token
    AUTH_TEMPLATE = '''{{"id":"{id}","key":"{key}"}}'''

    def __init__(self, typ, **kwargs):
        # Make sure required elements are present
        get_config_element(CFG_TRANSPORT_HTTPS_AUTH_URL,
                           kwargs, CFG_PROPERTIES)
        get_config_element(CFG_URL,
                           kwargs, CFG_PROPERTIES)
        get_config_element(CFG_TRANSPORT_HTTPS_JWT_ID,
                           kwargs, CFG_PROPERTIES)
        get_config_element(CFG_TRANSPORT_HTTPS_JWT_KEY,
                           kwargs, CFG_PROPERTIES)
        super().__init__(typ, **kwargs)

        self.jwt_token = (None, None)
        self.session = requests.session()
        if not self.verify_ssl():
            self.session.mount('https://', host_header_ssl.HostHeaderSSLAdapter())
        self.auth_ttl = self.jwt_token_ttl_minutes()
        self.logger = None

    def _init_logger(self):
        if self.logger is None:
            # Avoid circular imports
            from sensors.common import logging
            self.logger = logging.get_instance()

    def transmit(self, repo: SqliteRepository):
        self._init_logger()
        obs = repo.get_observations()
        if obs is None:
            self.logger.warn("Transmitter: unable to read observations from DB, giving up for now.")
            return
        self.logger.debug("Transmitter: read {0} observations from DB.".format(len(obs)))
        if len(obs) > 0:
            # Serialize observations to SensorThings dataArray JSON
            obs_dict = observations_list_to_dict(obs)

            sample_type = os.environ.get('SAMPLE_TYPE')
            if sample_type == "AVERAGE":
                original_json = observations_to_json(obs_dict)
                # Get the multidatastream_id from the env var set by balenaCloud
                multidatastream_id = os.environ.get('MULTIDATASTREAM_ID')
                if multidatastream_id == "null":
                    self.logger.info("Transmitter: MULTIDATASTREAM_ID is not defined. Sending RAW values instead.")
                else:
                    for datastream in obs_dict:
                        try:
                            datastream['MultiDatastream']
                        except KeyError:
                            continue
                        if datastream['MultiDatastream']['@iot.id'] == multidatastream_id:
                            self.logger.debug("Transmitter: found a matching multidatastream.")
                            total_temp = 0
                            total_humidity = 0
                            for data in datastream['dataArray']:
                                total_temp += data[1][0]
                                total_humidity += data[1][1]
                            avg_temp = round((total_temp / len(datastream['dataArray'])))
                            avg_humidity = round((total_humidity / len(datastream['dataArray'])))

                            # Rebuild the dataArray with only the avg values
                            datastream['dataArray'] = [datastream['dataArray'][len(datastream['dataArray']) - 1][0], [avg_temp, avg_humidity], {}]
                json = observations_to_json(obs_dict)
                self.logger.debug("Transmitter: original JSON payload: {0}".format(original_json))
                self.logger.debug("Transmitter: new avg JSON payload: {0}".format(json))
            else:
                json = observations_to_json(obs_dict)
                self.logger.debug("Transmitter: JSON payload: {0}".format(json))

            # POST observations
            self._jwt_authenticate()
            url = self._join_path_to_url(self.url(), self.STA_POST_PATH)
            headers = {'Content-Type': 'application/json',
                       'Authorization': "Bearer {token}".format(token=self.jwt_token[0])}
            self.logger.debug("Transmitter: Posting data to {0}...".format(url))
            try:
                r = self.session.post(url, headers=headers, data=json, verify=self.verify_ssl())
            except ConnectionError as e:
                raise TransmissionException("POST failed due to error: {0}".format(str(e)))
            self.logger.debug("Transmitter: Status code was {0}".format(r.status_code))
            if r.status_code != self.SUCCESS_STATUS_CODE:
                raise TransmissionException("Transmission failed with status code: {0}".format(r.status_code))

            # Remove observations from local data, unless the observation could not be
            #   created, then update its status to error.
            ids_to_delete = []
            ids_to_update_status = []
            err_mesgs = []

            for (i, e) in enumerate(r.json()):
                if e.startswith(self.ERROR_RESPONSE):
                    ids_to_update_status.append(obs[i].id)
                    err_mesgs.append(e)
                else:
                    ids_to_delete.append(obs[i].id)

            repo.delete_observations(ids_to_delete)
            self.logger.debug("Transmitter: Successfully submitted {0} observations.".format(len(ids_to_delete)))
            if len(err_mesgs) > 0:
                repo.update_observation_status(ids_to_update_status, status=SqliteRepository.STATUS_ERROR)
                mesg = ("Transmitter: Failed to submit {0} observations, "
                        "due to errors: " + "; ".join(err_mesgs) + ". "
                        "which were retained in local database with status {1}.").format(len(ids_to_update_status),
                                                                                         SqliteRepository.STATUS_ERROR)
                self.logger.error(mesg)

    def _jwt_authenticate(self):
        self._init_logger()
        new_token = self.jwt_token
        auth_required = False

        # Figure out if authentication is required, that is: (1) if we have never authenticated (token_timestamp is None);
        #   or (2) token_timestamp is later than or equal to the current time + self.auth_ttl
        token_timestamp = self.jwt_token[1]
        if token_timestamp is None:
            self.logger.debug("Transmitter: Auth token is null, authenticating ...")
            auth_required = True
        else:
            token_expired_after = token_timestamp + self.auth_ttl
            if datetime.utcnow() >= token_expired_after:
                self.logger.debug("Transmitter: Auth token expired, re-authenticating ...")
                auth_required = True

        if auth_required:
            json = self.AUTH_TEMPLATE.format(id=self.jwt_id(), key=self.jwt_key())
            headers = {'Content-Type': 'application/json'}
            url = self.auth_url()
            try:
                r = self.session.post(url, headers=headers, data=json, verify=self.verify_ssl())
            except ConnectionError as e:
                raise AuthenticationException(
                    "Unable to authenticate to {0} due to error: {1}".format(url, str(e)))
            self.logger.debug(("Transmitter: Auth status code was {0}".format(r.status_code)))
            if r.status_code != 200:
                raise AuthenticationException("Authentication to URL {0} failed with status code {1}".
                                              format(url, str(r.status_code)))
            else:
                new_token = (r.json()["token"], datetime.utcnow())
            self.jwt_token = new_token

    @staticmethod
    def _join_path_to_url(url, path):
        final_url = url
        if final_url[-1] != '/' and path[0] != '/':
            final_url += '/'
        elif final_url[-1] == '/' and path[0] == '/':
            final_url = final_url.strip('/')
        final_url += path
        return final_url

    def identifier(self) -> str:
        return Transport.IDENTIFIER_SEPARATOR.join((self.typ, self.properties[CFG_URL]))

    def auth_url(self) -> str:
        return self.properties[CFG_TRANSPORT_HTTPS_AUTH_URL]

    def url(self) -> str:
        return self.properties[CFG_URL]

    def jwt_id(self) -> str:
        return self.properties[CFG_TRANSPORT_HTTPS_JWT_ID]

    def jwt_key(self) -> str:
        return self.properties[CFG_TRANSPORT_HTTPS_JWT_KEY]

    def verify_ssl(self) -> bool:
        return bool(self.properties.get(CFG_TRANSPORT_HTTPS_VERIFY_SSL,
                                        self.DEFAULT_VERIFY_SSL))

    def jwt_token_ttl_minutes(self) -> timedelta:
        return timedelta(minutes=int(self.properties.get(CFG_TRANSPORT_HTTPS_JWT_TTL, self.DEFAULT_JWT_TTL)))

