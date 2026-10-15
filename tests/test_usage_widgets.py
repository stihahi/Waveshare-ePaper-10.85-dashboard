import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from usage_widgets import draw_limit_accounts_widget

FONTS = {'20': 'font-20', '28': 'font-28'}
WINDOW = {"utilization": 16.0, "resets_at": None}


def drawn_texts(usages):
    draw = mock.MagicMock()
    draw_limit_accounts_widget(draw, FONTS, 0, 0, "CODEX USAGE", usages)
    return [call.args[1] for call in draw.text.call_args_list]


class DrawLimitAccountsWidgetTest(unittest.TestCase):
    def test_titles_the_widget_with_both_windows(self):
        self.assertEqual(drawn_texts({})[0], "CODEX USAGE  5h / 7d")

    def test_shows_both_windows_of_an_account(self):
        texts = drawn_texts({"sub": {"five_hour": {"utilization": 100.0, "resets_at": None}, "seven_day": WINDOW}})

        self.assertIn("100% N/A", texts)
        self.assertIn("16% N/A", texts)

    def test_marks_a_window_the_plan_does_not_report(self):
        texts = drawn_texts({"main": {"five_hour": None, "seven_day": WINDOW}})

        self.assertIn("not reported", texts)
        self.assertIn("16% N/A", texts)

    def test_shows_an_error_instead_of_windows_when_the_fetch_failed(self):
        texts = drawn_texts({"main": {"error": True}})

        self.assertEqual(texts[1:], ["main", "Usage Error"])


if __name__ == '__main__':
    unittest.main()
