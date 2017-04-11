import unittest
import os

import sensors.common.constants as constants
from sensors.domain.observation import Observation


class TestObservation(unittest.TestCase):

    def setUp(self):
        os.unlink(constants.DB_PATH)

    def test_parameters_serialization(self):
        o = Observation()
        parameters = {"one": "1", "two": "2"}
        o.set_parameters(**parameters)
        self.assertEquals(o.parameters["one"], "1")
        self.assertEquals(o.parameters["two"], "2")

        paramStr = o.get_parameters_as_json()
        self.assertEquals('"one":"1","two":"2"', paramStr)

        o.set_parameters_from_str(paramStr)
        self.assertEquals(len(o.parameters), 2)
        self.assertEquals(o.parameters["one"], "1")
        self.assertEquals(o.parameters["two"], "2")

if __name__ == '__main__':
    unittest.main()