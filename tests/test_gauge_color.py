import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from panel_frame import BLACK, RED, YELLOW
from usage_widgets import gauge_fill_color


class GaugeFillColorTest(unittest.TestCase):
    def test_normal_usage_is_black(self):
        self.assertEqual(gauge_fill_color(0), BLACK)
        self.assertEqual(gauge_fill_color(60), BLACK)

    def test_above_warning_threshold_is_yellow(self):
        self.assertEqual(gauge_fill_color(60.1), YELLOW)
        self.assertEqual(gauge_fill_color(80), YELLOW)

    def test_above_danger_threshold_is_red(self):
        self.assertEqual(gauge_fill_color(80.1), RED)
        self.assertEqual(gauge_fill_color(100), RED)


if __name__ == '__main__':
    unittest.main()
