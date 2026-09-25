import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import gmail_auth
from gmail_auth import authorization_code_from_callback, interactive_auth, load_usable_credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def stored_credentials(valid=True, refresh_token="refresh-token"):
    credentials = mock.MagicMock()
    credentials.valid = valid
    credentials.refresh_token = refresh_token
    credentials.to_json.return_value = json.dumps({"token": "refreshed"})
    return credentials


class AuthorizationCodeFromCallbackTest(unittest.TestCase):
    def test_extracts_code_from_redirected_url(self):
        url = "http://localhost/?state=abc&code=4/0AbC-dEf&scope=https://www.googleapis.com/auth/gmail.readonly"
        self.assertEqual(authorization_code_from_callback(url), "4/0AbC-dEf")

    def test_accepts_surrounding_whitespace(self):
        self.assertEqual(authorization_code_from_callback("  http://localhost/?code=xyz\n"), "xyz")

    def test_rejects_url_without_code(self):
        with self.assertRaises(ValueError):
            authorization_code_from_callback("http://localhost/?error=access_denied")


class CredentialsTestCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.token_path = Path(directory.name) / "token.json"
        self.credentials_path = Path(directory.name) / "credentials.json"

    def write_token(self):
        self.token_path.write_text(json.dumps({"token": "stored"}))

    def patch_stored(self, credentials):
        patcher = mock.patch.object(gmail_auth.Credentials, "from_authorized_user_file", return_value=credentials)
        self.addCleanup(patcher.stop)
        return patcher.start()


class LoadUsableCredentialsTest(CredentialsTestCase):
    def test_returns_nothing_when_no_token_was_stored(self):
        self.assertIsNone(load_usable_credentials(self.token_path, SCOPES))

    def test_returns_a_valid_token_unchanged(self):
        credentials = stored_credentials()
        self.write_token()
        self.patch_stored(credentials)

        self.assertIs(load_usable_credentials(self.token_path, SCOPES), credentials)

    def test_refreshes_an_expired_token_and_stores_it(self):
        credentials = stored_credentials(valid=False)
        self.write_token()
        self.patch_stored(credentials)

        self.assertIs(load_usable_credentials(self.token_path, SCOPES), credentials)
        credentials.refresh.assert_called_once()
        self.assertEqual(json.loads(self.token_path.read_text()), {"token": "refreshed"})

    def test_returns_nothing_when_the_token_was_revoked(self):
        credentials = stored_credentials(valid=False)
        credentials.refresh.side_effect = gmail_auth.RefreshError("invalid_grant: Token has been expired or revoked.")
        self.write_token()
        self.patch_stored(credentials)

        self.assertIsNone(load_usable_credentials(self.token_path, SCOPES))

    def test_returns_nothing_when_an_expired_token_cannot_be_refreshed(self):
        self.write_token()
        self.patch_stored(stored_credentials(valid=False, refresh_token=None))

        self.assertIsNone(load_usable_credentials(self.token_path, SCOPES))


class InteractiveAuthTest(CredentialsTestCase):
    def test_skips_the_consent_flow_while_the_token_works(self):
        self.write_token()
        self.patch_stored(stored_credentials())

        with mock.patch.object(gmail_auth, "_prompt_for_callback") as prompt:
            self.assertTrue(interactive_auth(self.credentials_path, self.token_path, SCOPES))
        prompt.assert_not_called()

    def test_asks_for_consent_again_when_the_token_was_revoked(self):
        credentials = stored_credentials(valid=False)
        credentials.refresh.side_effect = gmail_auth.RefreshError("invalid_grant")
        self.write_token()
        self.patch_stored(credentials)
        self.credentials_path.write_text(json.dumps({"installed": {"client_id": "x"}}))

        with mock.patch.object(gmail_auth, "_create_flow"), \
             mock.patch.object(gmail_auth, "_prompt_for_callback", return_value="") as prompt:
            self.assertFalse(interactive_auth(self.credentials_path, self.token_path, SCOPES))
        prompt.assert_called_once()


if __name__ == '__main__':
    unittest.main()
