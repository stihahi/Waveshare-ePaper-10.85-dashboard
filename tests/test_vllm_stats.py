import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from vllm_stats import VllmActivity, VllmStats, parse_engine_log_line, summarize_samples

LOG_LINE = ("(APIServer pid=1222) INFO 09-17 18:27:24 [loggers.py:310] Engine 000: "
            "Avg prompt throughput: 120.5 tokens/s, Avg generation throughput: 14.6 tokens/s, "
            "Running: 3 reqs, Waiting: 2 reqs, GPU KV cache usage: 7.0%, "
            "Prefix cache hit rate: 23.6%, MM cache hit rate: 0.0%")


def sample(prompt=0.0, generation=0.0, running=0, waiting=0, kv_cache=0.0):
    return VllmStats(prompt_throughput=prompt, generation_throughput=generation,
                     running=running, waiting=waiting, kv_cache_pct=kv_cache)


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


class SummarizeSamplesTest(unittest.TestCase):
    def test_averages_throughputs_over_samples_that_served_requests(self):
        samples = [sample(prompt=2740.0, generation=0.4, running=2),
                   sample(prompt=0.0, generation=114.0, running=4),
                   sample(prompt=0.0, generation=158.0, running=4)]

        activity = summarize_samples(samples)

        self.assertAlmostEqual(activity.mean_generation_throughput, 90.8)
        self.assertAlmostEqual(activity.mean_prompt_throughput, 913.3333, places=3)

    def test_ignores_idle_samples_when_averaging(self):
        samples = [sample(running=0), sample(prompt=100.0, generation=20.0, running=1)]

        self.assertAlmostEqual(summarize_samples(samples).mean_generation_throughput, 20.0)

    def test_queue_state_comes_from_the_newest_sample(self):
        samples = [sample(generation=150.0, running=4, waiting=2, kv_cache=11.0),
                   sample(generation=70.0, running=1, waiting=0, kv_cache=3.5)]

        activity = summarize_samples(samples)

        self.assertEqual((activity.running, activity.waiting, activity.kv_cache_pct), (1, 0, 3.5))

    def test_idle_window_reports_zero_throughput(self):
        self.assertEqual(summarize_samples([sample(running=0), sample(running=0)]),
                         VllmActivity(mean_prompt_throughput=0.0, mean_generation_throughput=0.0,
                                      running=0, waiting=0, kv_cache_pct=0.0))

    def test_rejects_an_empty_window(self):
        with self.assertRaises(ValueError):
            summarize_samples([])


if __name__ == '__main__':
    unittest.main()
