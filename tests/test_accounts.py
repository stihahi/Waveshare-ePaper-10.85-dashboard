import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from accounts import SCRIPT_DIR, account_file, account_from_argv


class AccountFileTest(unittest.TestCase):
    def test_builds_per_account_json_next_to_scripts(self):
        self.assertEqual(account_file("claude_creds", "work"), SCRIPT_DIR / "claude_creds_work.json")

    def test_allows_digits_hyphen_and_underscore(self):
        self.assertEqual(account_file("usage", "acct-1_b").name, "usage_acct-1_b.json")

    def test_rejects_names_that_escape_the_directory(self):
        for bad_name in ("../x", "a/b", "", "with space"):
            with self.subTest(bad_name=bad_name):
                with self.assertRaises(ValueError):
                    account_file("usage", bad_name)


class AccountFromArgvTest(unittest.TestCase):
    def test_reads_value_after_account_flag(self):
        self.assertEqual(account_from_argv(["codex.py", "--once", "--account", "work"]), "work")

    def test_requires_account_flag(self):
        with self.assertRaises(ValueError):
            account_from_argv(["codex.py", "--once"])

    def test_requires_value_after_flag(self):
        with self.assertRaises(ValueError):
            account_from_argv(["codex.py", "--account"])


if __name__ == '__main__':
    unittest.main()
