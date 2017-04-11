import os
import unittest

import sensors.common.constants as constants
from sensors.domain.observation import Observation
from sensors.persistence.sqlite import SqliteRepository


class TestSqliteRepository(unittest.TestCase):

    def setUp(self):
        try:
            os.unlink(constants.DB_PATH)
        except FileNotFoundError:
            pass

    def test_rw_observations(self):
        repo = SqliteRepository()

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

        obs = repo.get_observations()
        self.assertEquals(2, len(obs))
        self.assertTrue(o1, obs[0])
        self.assertTrue(o2, obs[1])

        ids_to_delete = [o.id for o in obs]
        repo.delete_observations(ids_to_delete)

        obs = repo.get_observations()
        self.assertEquals(0, len(obs))

if __name__ == '__main__':
    unittest.main()