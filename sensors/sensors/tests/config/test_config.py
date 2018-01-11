import os
import unittest

from sensors.config import load_config, ConfigurationError
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

    def test_config_one_dupe_ds_id(self):
        os.environ[ENV_YAML_PATH] = '../data/config1-dupe-ds_id.yml'
        with self.assertRaises(ConfigurationError):
            c = load_config()

    def test_config_one_dupe_transport(self):
        os.environ[ENV_YAML_PATH] = '../data/config1-dupe-transport.yml'
        with self.assertRaises(ConfigurationError):
            c = load_config()


if __name__ == '__main__':
    unittest.main()
