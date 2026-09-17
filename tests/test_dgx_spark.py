import os
import sys
import subprocess
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from dgx_spark import GpuStatus, GpuUnavailable, parse_gpu_status, query_gpu_status


class ParseGpuStatusTest(unittest.TestCase):
    def test_reads_temperature_and_utilization(self):
        self.assertEqual(parse_gpu_status("65, 96\n"), GpuStatus(temperature_c=65, utilization_pct=96))

    def test_uses_first_gpu_when_several_lines(self):
        self.assertEqual(parse_gpu_status("40, 3\n70, 99\n"), GpuStatus(temperature_c=40, utilization_pct=3))

    def test_rejects_unsupported_values(self):
        with self.assertRaises(ValueError):
            parse_gpu_status("[N/A], 12")

    def test_rejects_empty_output(self):
        with self.assertRaises(ValueError):
            parse_gpu_status("")


class QueryGpuStatusTest(unittest.TestCase):
    def test_unreachable_host_is_reported_offline(self):
        with mock.patch("dgx_spark.subprocess.run", side_effect=subprocess.CalledProcessError(255, "ssh")):
            self.assertIs(query_gpu_status("spark-x"), GpuUnavailable.OFFLINE)


if __name__ == '__main__':
    unittest.main()
