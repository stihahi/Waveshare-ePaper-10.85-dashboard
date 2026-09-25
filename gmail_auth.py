# Gmail login for a headless Pi: reuse the stored token while it still works,
# otherwise print the consent URL, let the user paste back the (unreachable)
# localhost redirect URL, and save token.json.
import os
from urllib.parse import parse_qs, urlparse

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

LOOPBACK_REDIRECT_URI = "http://localhost"


def authorization_code_from_callback(callback_url):
    codes = parse_qs(urlparse(callback_url.strip()).query).get("code")
    if not codes:
        raise ValueError("callback URL does not contain an authorization code")
    return codes[0]


def load_usable_credentials(token_path, scopes):
    if not os.path.exists(token_path):
        return None
    credentials = Credentials.from_authorized_user_file(str(token_path), scopes)
    if credentials.valid:
        return credentials
    return _refreshed(credentials, token_path)


def _refreshed(credentials, token_path):
    if not credentials.refresh_token:
        return None
    try:
        credentials.refresh(Request())
    except RefreshError as error:
        print(f"Stored Gmail token is no longer usable: {error}")
        return None
    _store_token(token_path, credentials)
    return credentials


def interactive_auth(credentials_path, token_path, scopes):
    if load_usable_credentials(token_path, scopes):
        return True
    if not os.path.exists(credentials_path):
        print(f"{os.path.basename(credentials_path)} not found. Gmail widget shows 0.")
        return False
    flow = _create_flow(credentials_path, scopes)
    callback_url = _prompt_for_callback(flow)
    if not callback_url:
        print("Gmail authorization skipped.\n")
        return False
    return _save_token(flow, callback_url, token_path)


def _create_flow(credentials_path, scopes):
    from google_auth_oauthlib.flow import InstalledAppFlow
    return InstalledAppFlow.from_client_secrets_file(credentials_path, scopes, redirect_uri=LOOPBACK_REDIRECT_URI)


def _prompt_for_callback(flow):
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    print("\n" + "=" * 60)
    print("  GMAIL AUTHORIZATION REQUIRED")
    print("=" * 60)
    print(f"\n1. Open this URL in any browser:\n\n   {auth_url}\n")
    print("2. Log in and allow read-only Gmail access.")
    print("3. The browser ends on an unreachable http://localhost/?...code=... page.")
    print("   Copy that FULL URL from the address bar.\n")
    return input("Paste the full callback URL here (or press Enter to skip): ").strip()


def _save_token(flow, callback_url, token_path):
    try:
        flow.fetch_token(code=authorization_code_from_callback(callback_url))
    except Exception as error:
        print(f"Gmail authorization failed: {error}")
        return False
    _store_token(token_path, flow.credentials)
    print("Gmail Authorization Successful!\n")
    return True


def _store_token(token_path, credentials):
    with open(token_path, "w") as token_file:
        token_file.write(credentials.to_json())
    os.chmod(token_path, 0o600)
