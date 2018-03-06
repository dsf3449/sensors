import sqlite3

from sensors.common.constants import CFG_SPOOLER_DB_PATH
from sensors.domain.observation import Observation
from sensors.common import logging


class SqliteRepository:

    STATUS_PENDING = "PENDING"
    STATUS_ERROR = "ERROR"

    SQL_CREATE_OBS_TABLE = '''CREATE TABLE IF NOT EXISTS observation 
    (id INTEGER PRIMARY KEY ASC,
    featureOfInterestId TEXT,
    datastreamId TEXT NOT NULL,
    phenomenonTime DATETIME,
    result TEXT NOT NULL,
    parameters TEXT,
    status TEXT NOT NULL CHECK (status="PENDING" or status="ERROR") DEFAULT "PENDING")
    '''
    SQL_CREATE_OBS = ("INSERT INTO observation "
                      "(featureOfInterestId, datastreamId, phenomenonTime, result, parameters) "
                      "VALUES (?, ?, ?, ?, ?)"
                      )
    SQL_GET_OBS = 'SELECT * FROM observation WHERE status="PENDING" LIMIT ?'
    SQL_GET_ALL_OBS = 'SELECT * FROM observation'
    SQL_DELETE_OBS = "DELETE FROM observation WHERE id IN ({0})"
    SQL_UPDATE_STATUS = 'UPDATE observation SET status="{0}" WHERE id IN ({1})'

    MAX_RETRIES = 5

    def _perform_action_with_connection(self, action):
        with sqlite3.connect(self.db_path) as conn:
            action(conn)
            conn.commit()

    def __init__(self, config):
        self.db_path = config[CFG_SPOOLER_DB_PATH]
        self._perform_action_with_connection(SqliteRepository._create_tables)
        self.logger = logging.get_instance()

    @staticmethod
    def _create_tables(conn):
        cursor = conn.cursor()
        SqliteRepository._create_observation_table(cursor)
        cursor.close()

    @staticmethod
    def _create_observation_table(cursor):
        cursor.execute(SqliteRepository.SQL_CREATE_OBS_TABLE)

    def create_observation(self, o):
        observation = (o.featureOfInterestId, o.datastreamId,
                       o.phenomenonTime, o.result, o.get_parameters_as_str())
        self._perform_action_with_connection(lambda c: c.execute(SqliteRepository.SQL_CREATE_OBS,
                                                                 observation))

    def get_observations(self, limit="360"):
        observations = []

        attempts = 1
        with sqlite3.connect(self.db_path) as conn:
            while attempts < self.MAX_RETRIES:
                attempts += 1
                try:
                    for r in conn.execute(SqliteRepository.SQL_GET_OBS, (limit,)):
                        o = Observation()
                        o.id = r[0]
                        o.featureOfInterestId = r[1]
                        o.datastreamId = r[2]
                        o.phenomenonTime = r[3]
                        o.result = r[4]
                        o.set_parameters_from_str(r[5])
                        observations.append(o)
                    break
                except sqlite3.OperationalError as e:
                    self.logger.warn("Error encountered reading observations from SQLite database, error was: {0}"
                                     ", will re-try {1} times...".
                                     format(str(e), self.MAX_RETRIES))
                    if attempts >= self.MAX_RETRIES:
                        observations = None
                        break

        return observations

    def delete_observations(self, ids):
        with sqlite3.connect(self.db_path) as conn:
            id_str = ",".join([str(i) for i in ids])
            # We control the input, so it is not so un-safe to forgo binding parameters
            conn.execute(SqliteRepository.SQL_DELETE_OBS.format(id_str))
            conn.commit()

    def update_observation_status(self, ids, status=STATUS_ERROR):
        with sqlite3.connect(self.db_path) as conn:
            id_str = ",".join([str(i) for i in ids])
            # We control the input, so it is not so un-safe to forgo binding parameters
            conn.execute(SqliteRepository.SQL_UPDATE_STATUS.format(status, id_str))
            conn.commit()

    def get_all_observations(self):
        observations = []

        with sqlite3.connect(self.db_path) as conn:
            for r in conn.execute(SqliteRepository.SQL_GET_ALL_OBS):
                o = Observation()
                o.id = r[0]
                o.featureOfInterestId = r[1]
                o.datastreamId = r[2]
                o.phenomenonTime = r[3]
                o.result = r[4]
                o.set_parameters_from_str(r[5])
                observations.append(o)
            conn.commit()

        return observations
