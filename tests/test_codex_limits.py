import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from codex import extract_limits

FIVE_HOURS = 5 * 60 * 60
SEVEN_DAYS = 7 * 24 * 60 * 60


def window(used_percent, seconds, reset_at=1792689429):
    return {"used_percent": used_percent, "limit_window_seconds": seconds, "reset_at": reset_at}


class ExtractLimitsTest(unittest.TestCase):
    def test_reads_both_windows_when_the_plan_has_a_five_hour_limit(self):
        raw = {"rate_limit": {"primary_window": window(100, FIVE_HOURS), "secondary_window": window(16, SEVEN_DAYS)}}

        five_hour, seven_day = extract_limits(raw)

        self.assertEqual(five_hour["utilization"], 100.0)
        self.assertEqual(seven_day["utilization"], 16.0)

    def test_reports_no_five_hour_window_when_the_plan_only_has_a_weekly_limit(self):
        raw = {"rate_limit": {"primary_window": window(3, SEVEN_DAYS), "secondary_window": None}}

        five_hour, seven_day = extract_limits(raw)

        self.assertIsNone(five_hour)
        self.assertEqual(seven_day["utilization"], 3.0)


if __name__ == '__main__':
    unittest.main()
