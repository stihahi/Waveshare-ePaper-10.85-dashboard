import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from local_config import LocalConfig, Location, load_local_config

DEFAULT = LocalConfig(location=Location(latitude=1.5, longitude=-2.5), dgx_spark_hosts={'default': 'default-host'})


class LoadLocalConfigTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / 'local_config.json'

    def write_config(self, config):
        self.path.write_text(json.dumps(config))

    def test_reads_location_and_dgx_spark_hosts(self):
        self.write_config({'location': {'latitude': 35.68, 'longitude': 139.76},
                           'dgx_spark_hosts': {'dgx1': 'host-a', 'dgx2': 'host-b'}})
        self.assertEqual(load_local_config(self.path, DEFAULT),
                         LocalConfig(location=Location(latitude=35.68, longitude=139.76),
                                     dgx_spark_hosts={'dgx1': 'host-a', 'dgx2': 'host-b'}))

    def test_falls_back_to_default_when_file_is_missing(self):
        self.assertEqual(load_local_config(self.path, DEFAULT), DEFAULT)

    def test_falls_back_per_section_when_section_is_omitted(self):
        self.write_config({'dgx_spark_hosts': {'dgx1': 'host-a'}})
        self.assertEqual(load_local_config(self.path, DEFAULT),
                         LocalConfig(location=DEFAULT.location, dgx_spark_hosts={'dgx1': 'host-a'}))

    def test_rejects_location_without_longitude(self):
        self.write_config({'location': {'latitude': 35.68}})
        with self.assertRaises(KeyError):
            load_local_config(self.path, DEFAULT)


if __name__ == '__main__':
    unittest.main()
