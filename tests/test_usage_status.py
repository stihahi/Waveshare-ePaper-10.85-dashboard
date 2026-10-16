import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from usage_status import UsageProblem, usage_problem

WINDOW = {"utilization": 40, "resets_at": "2026-09-18T00:00:00+00:00"}


class UsageProblemTest(unittest.TestCase):
    def test_usage_with_both_windows_has_no_problem(self):
        self.assertIsNone(usage_problem({"five_hour": WINDOW, "seven_day": WINDOW}))

    def test_a_plan_without_a_five_hour_window_has_no_problem(self):
        self.assertIsNone(usage_problem({"five_hour": None, "seven_day": WINDOW}))

    def test_a_plan_without_a_weekly_window_has_no_problem(self):
        self.assertIsNone(usage_problem({"five_hour": WINDOW, "seven_day": None}))

    def test_a_rejected_login_asks_for_a_new_login(self):
        self.assertIs(usage_problem({"error": "login_expired"}), UsageProblem.LOGIN_EXPIRED)

    def test_any_other_error_is_a_failed_fetch(self):
        self.assertIs(usage_problem({"error": "fetch_failed"}), UsageProblem.FETCH_FAILED)

    def test_no_window_at_all_is_a_failed_fetch(self):
        self.assertIs(usage_problem({"five_hour": None, "seven_day": None}), UsageProblem.FETCH_FAILED)

    def test_a_missing_file_is_a_failed_fetch(self):
        self.assertIs(usage_problem(None), UsageProblem.FETCH_FAILED)


if __name__ == '__main__':
    unittest.main()
