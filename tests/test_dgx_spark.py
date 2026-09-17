import os
import sys
import subprocess
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from dgx_spark import GpuStatus, GpuUnavailable, NodeMetrics, parse_gpu_status, parse_node_metrics, query_node_metrics


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


GPU_ONLY_OUTPUT = "temperature_c=54\nutilization_pct=0\n"
FULL_OUTPUT = GPU_ONLY_OUTPUT + (
    "model=nvidia/GLM-5.3-Flash-NVFP4\n"
    "vllm=(APIServer pid=1222) INFO 09-17 18:27:24 [loggers.py:310] Engine 000: "
    "Avg prompt throughput: 0.0 tokens/s, Avg generation throughput: 14.6 tokens/s, "
    "Running: 1 reqs, Waiting: 0 reqs, GPU KV cache usage: 7.0%, Prefix cache hit rate: 23.6%\n"
)


class ParseNodeMetricsTest(unittest.TestCase):
    def test_reads_gpu_and_engine_stats(self):
        metrics = parse_node_metrics(FULL_OUTPUT)

        self.assertEqual(metrics.gpu, GpuStatus(temperature_c=54, utilization_pct=0))
        self.assertEqual(metrics.model, "nvidia/GLM-5.3-Flash-NVFP4")
        self.assertEqual(metrics.vllm.generation_throughput, 14.6)
        self.assertEqual(metrics.vllm.running, 1)

    def test_node_without_engine_reports_gpu_only(self):
        metrics = parse_node_metrics(GPU_ONLY_OUTPUT)

        self.assertEqual(metrics.gpu, GpuStatus(temperature_c=54, utilization_pct=0))
        self.assertIsNone(metrics.model)
        self.assertIsNone(metrics.vllm)

    def test_rejects_output_without_gpu_fields(self):
        with self.assertRaises(ValueError):
            parse_node_metrics("model=x\n")


class QueryNodeMetricsTest(unittest.TestCase):
    def test_unreachable_host_is_reported_offline(self):
        with mock.patch("dgx_spark.subprocess.run", side_effect=subprocess.CalledProcessError(255, "ssh")):
            self.assertEqual(query_node_metrics("spark-x"), NodeMetrics(gpu=GpuUnavailable.OFFLINE))


if __name__ == '__main__':
    unittest.main()
