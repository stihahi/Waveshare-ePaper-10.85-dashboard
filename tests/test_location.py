import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from location import Location, load_location

DEFAULT = Location(latitude=1.5, longitude=-2.5)


class LoadLocationTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / 'location.json'

    def test_reads_coordinates_from_file(self):
        self.path.write_text(json.dumps({'latitude': 35.68, 'longitude': 139.76}))
        self.assertEqual(load_location(self.path, DEFAULT), Location(latitude=35.68, longitude=139.76))

    def test_falls_back_to_default_when_file_is_missing(self):
        self.assertEqual(load_location(self.path, DEFAULT), DEFAULT)

    def test_rejects_file_without_longitude(self):
        self.path.write_text(json.dumps({'latitude': 35.68}))
        with self.assertRaises(KeyError):
            load_location(self.path, DEFAULT)


if __name__ == '__main__':
    unittest.main()
