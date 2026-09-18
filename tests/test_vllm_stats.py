import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from vllm_stats import VllmStats, parse_engine_log_line

LOG_LINE = ("(APIServer pid=1222) INFO 09-17 18:27:24 [loggers.py:310] Engine 000: "
            "Avg prompt throughput: 120.5 tokens/s, Avg generation throughput: 14.6 tokens/s, "
            "Running: 3 reqs, Waiting: 2 reqs, GPU KV cache usage: 7.0%, "
            "Prefix cache hit rate: 23.6%, MM cache hit rate: 0.0%")


class ParseEngineLogLineTest(unittest.TestCase):
    def test_reads_every_monitored_field(self):
        self.assertEqual(
            parse_engine_log_line(LOG_LINE),
            VllmStats(prompt_throughput=120.5, generation_throughput=14.6, running=3, waiting=2, kv_cache_pct=7.0),
        )

    def test_reads_an_idle_engine(self):
        idle = LOG_LINE.replace("120.5", "0.0").replace("14.6", "0.0").replace("Running: 3", "Running: 0")
        self.assertEqual(parse_engine_log_line(idle).generation_throughput, 0.0)
        self.assertEqual(parse_engine_log_line(idle).running, 0)

    def test_rejects_an_unrelated_line(self):
        with self.assertRaises(ValueError):
            parse_engine_log_line("INFO 09-17 18:29:04 Starting vLLM API server")

    def test_rejects_a_truncated_line(self):
        with self.assertRaises(ValueError):
            parse_engine_log_line("Engine 000: Avg prompt throughput: 0.0 tokens/s, Running: 1 reqs")


if __name__ == '__main__':
    unittest.main()
