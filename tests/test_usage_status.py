import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from usage_status import claude_usage_failed, codex_usage_failed

WINDOW = {"utilization": 40, "resets_at": "2026-09-18T00:00:00+00:00"}


class ClaudeUsageFailedTest(unittest.TestCase):
    def test_valid_usage_is_not_failure(self):
        self.assertFalse(claude_usage_failed({"five_hour": WINDOW, "seven_day": WINDOW}))

    def test_error_payload_is_failure(self):
        self.assertTrue(claude_usage_failed({"error": "fetch_failed"}))

    def test_missing_file_is_failure(self):
        self.assertTrue(claude_usage_failed(None))


class CodexUsageFailedTest(unittest.TestCase):
    def test_valid_usage_is_not_failure(self):
        self.assertFalse(codex_usage_failed({"five_hour": WINDOW, "seven_day": WINDOW}))

    def test_negative_utilization_marks_failure(self):
        self.assertTrue(codex_usage_failed({"seven_day": {"utilization": -1.0, "resets_at": None}}))

    def test_missing_seven_day_is_failure(self):
        self.assertTrue(codex_usage_failed({"five_hour": WINDOW}))

    def test_missing_file_is_failure(self):
        self.assertTrue(codex_usage_failed(None))


if __name__ == '__main__':
    unittest.main()
