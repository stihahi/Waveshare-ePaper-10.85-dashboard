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
def engine_log_line(prompt, generation, running):
    return ("vllm=(APIServer pid=1222) INFO 09-17 18:27:24 [loggers.py:310] Engine 000: "
            f"Avg prompt throughput: {prompt} tokens/s, Avg generation throughput: {generation} tokens/s, "
            f"Running: {running} reqs, Waiting: 0 reqs, GPU KV cache usage: 7.0%, Prefix cache hit rate: 23.6%\n")


FULL_OUTPUT = GPU_ONLY_OUTPUT + "model=nvidia/GLM-5.3-Flash-NVFP4\n" + engine_log_line(0.0, 14.6, 1)
WINDOWED_OUTPUT = GPU_ONLY_OUTPUT + "model=nvidia/GLM-5.3-Flash-NVFP4\n" + "".join(
    (engine_log_line(2740.0, 0.4, 2), engine_log_line(0.0, 114.0, 4), engine_log_line(0.0, 158.0, 4)))


class ParseNodeMetricsTest(unittest.TestCase):
    def test_reads_gpu_and_engine_stats(self):
        metrics = parse_node_metrics(FULL_OUTPUT)

        self.assertEqual(metrics.gpu, GpuStatus(temperature_c=54, utilization_pct=0))
        self.assertEqual(metrics.model, "nvidia/GLM-5.3-Flash-NVFP4")
        self.assertEqual(metrics.vllm.mean_generation_throughput, 14.6)
        self.assertEqual(metrics.vllm.running, 1)

    def test_averages_the_engine_log_window(self):
        metrics = parse_node_metrics(WINDOWED_OUTPUT)

        self.assertAlmostEqual(metrics.vllm.mean_generation_throughput, 90.8)
        self.assertAlmostEqual(metrics.vllm.mean_prompt_throughput, 913.3333, places=3)
        self.assertEqual(metrics.vllm.running, 4)

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
