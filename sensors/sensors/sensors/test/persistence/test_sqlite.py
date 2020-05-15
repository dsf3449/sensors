import os
import unittest

from sensors.common.constants import *
from sensors.config import Config
from sensors.domain.observation import Observation
from sensors.domain.multiobservation import MultiObservation
from sensors.persistence.sqlite import SqliteRepository


class TestSqliteRepository(unittest.TestCase):

    config = None

    def setUp(self):
        os.environ[ENV_YAML_PATH] = './test_sqlite.yml'
        global config
        config = Config(unittest=True).config

        try:
            os.unlink(config[CFG_SPOOLER_DB_PATH])
        except FileNotFoundError:
            pass

    def test_rw_observations(self):

        repo = SqliteRepository(config)

        o1 = Observation()
        o1.featureOfInterestId = "12345"
        o1.datastreamId = "54321"
        o1.phenomenonTime = "2017-04-11T15:29:55Z"
        o1.result = "42.24"
        parameters = {"one": "1", "two": "2"}
        o1.set_parameters(**parameters)
        repo.create_observation(o1)

        o2 = Observation()
        o2.featureOfInterestId = "6789"
        o2.datastreamId = "9876"
        o2.phenomenonTime = "2017-04-11T15:32:25Z"
        o2.result = "23.32"
        parameters = {"three": "3", "four": "4"}
        o2.set_parameters(**parameters)
        repo.create_observation(o2)

        mo1 = MultiObservation()
        mo1.featureOfInterestId = "abcde"
        mo1.multidatastreamId = "1q2w3"
        mo1.phenomenonTime = "2017-04-11T15:35:55Z"
        mo1.result = [0.1, 0.2, 0.3]
        parameters = {"five": "5", "six": "6"}
        mo1.set_parameters(**parameters)
        repo.create_multiobservation(mo1)

        mo2 = MultiObservation()
        mo2.featureOfInterestId = "fghij"
        mo2.multidatastreamId = "p0o9i8"
        mo2.phenomenonTime = "2017-04-11T15:37:55Z"
        mo2.result = [0.4, 0.5, 0.6]
        parameters = {"seven": "7", "eight": "8"}
        mo2.set_parameters(**parameters)
        repo.create_multiobservation(mo2)

        obs = repo.get_observations()
        self.assertEqual(4, len(obs))
        self.assertTrue(isinstance(obs[0], Observation))
        self.assertTrue(o1, obs[0])
        self.assertTrue(isinstance(obs[1], Observation))
        self.assertTrue(o2, obs[1])
        self.assertTrue(isinstance(obs[2], MultiObservation))
        self.assertTrue(mo1, obs[2])
        self.assertTrue(isinstance(obs[3], MultiObservation))
        self.assertTrue(mo2, obs[3])

        ids_to_delete = [obs[0].id, obs[2].id]
        repo.delete_observations(ids_to_delete)

        ids_to_update = [obs[1].id, obs[3].id]
        repo.update_observation_status(ids_to_update)

        obs = repo.get_observations()
        self.assertEqual(0, len(obs))

        obs = repo.get_all_observations()
        self.assertEqual(2, len(obs))


if __name__ == '__main__':
    unittest.main()
