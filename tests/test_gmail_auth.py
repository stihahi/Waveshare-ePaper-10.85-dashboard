import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from gmail_auth import authorization_code_from_callback


class AuthorizationCodeFromCallbackTest(unittest.TestCase):
    def test_extracts_code_from_redirected_url(self):
        url = "http://localhost/?state=abc&code=4/0AbC-dEf&scope=https://www.googleapis.com/auth/gmail.readonly"
        self.assertEqual(authorization_code_from_callback(url), "4/0AbC-dEf")

    def test_accepts_surrounding_whitespace(self):
        self.assertEqual(authorization_code_from_callback("  http://localhost/?code=xyz\n"), "xyz")

    def test_rejects_url_without_code(self):
        with self.assertRaises(ValueError):
            authorization_code_from_callback("http://localhost/?error=access_denied")


if __name__ == '__main__':
    unittest.main()
