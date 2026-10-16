import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import claude
import codex
from usage_status import LoginExpired

EXPIRED_GRANT = '{"error": "invalid_grant", "error_description": "Refresh token expired"}'


def token_response(status_code, text):
    response = mock.MagicMock(status_code=status_code, text=text)
    response.json.return_value = {"access_token": "new-access", "expires_in": 28800}
    return response


class AccountDirectoryTestCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)


class ClaudeRefreshTest(AccountDirectoryTestCase):
    def refresh(self, response):
        files = claude.ClaudeAccountFiles(credentials=self.directory / "creds.json", usage=self.directory / "usage.json")
        with mock.patch.object(claude.requests, "post", return_value=response):
            return claude.refresh_access_token({"refreshToken": "stored"}, files)

    def test_a_rejected_refresh_token_means_the_login_expired(self):
        with self.assertRaises(LoginExpired):
            self.refresh(token_response(400, EXPIRED_GRANT))

    def test_a_server_error_is_only_a_failed_refresh(self):
        self.assertIsNone(self.refresh(token_response(500, "upstream error")))

    def test_a_successful_refresh_stores_the_new_access_token(self):
        self.assertEqual(self.refresh(token_response(200, ""))["accessToken"], "new-access")


class CodexRefreshTest(AccountDirectoryTestCase):
    def refresh(self, response):
        files = codex.CodexAccountFiles(account="sub", auth=self.directory / "auth.json", usage=self.directory / "usage.json")
        with mock.patch.object(codex.requests, "post", return_value=response):
            return codex.refresh_tokens({"tokens": {"refresh_token": "stored"}}, files)

    def test_a_rejected_refresh_token_means_the_login_expired(self):
        with self.assertRaises(LoginExpired):
            self.refresh(token_response(401, '{"error": {"code": "invalid_refresh_token"}}'))

    def test_a_server_error_is_only_a_failed_refresh(self):
        with self.assertRaises(codex.FatalError) as raised:
            self.refresh(token_response(500, "upstream error"))
        self.assertNotIsInstance(raised.exception, LoginExpired)


if __name__ == '__main__':
    unittest.main()
