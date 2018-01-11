import os
import unittest

from sensors.config import load_config
from sensors.config.constants import *
from sensors.domain.thing import Thing


class TestConfiguration(unittest.TestCase):

    def test_config_one(self):
        os.environ[ENV_YAML_PATH] = '../data/config1.yml'
        c = load_config()

        self.assertTrue(CFG_THING in c)
        t: Thing = c[CFG_THING]
        self.assertEqual(t.thing_id, '5474a427-f565-4233-8f82-a8178534b150')
        self.assertEqual(t.location_id, 'f5610fb9-1556-42d8-862c-1d290a9b5c58')

if __name__ == '__main__':
    unittest.main()
