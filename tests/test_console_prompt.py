import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from console_prompt import ask


class AskTest(unittest.TestCase):
    def test_returns_the_trimmed_answer(self):
        with mock.patch("builtins.input", return_value="  http://localhost/?code=abc \n"):
            self.assertEqual(ask("Paste: "), "http://localhost/?code=abc")

    def test_treats_a_missing_terminal_as_declining(self):
        with mock.patch("builtins.input", side_effect=EOFError):
            self.assertEqual(ask("Paste: "), "")


if __name__ == '__main__':
    unittest.main()
