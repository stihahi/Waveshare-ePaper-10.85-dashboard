# One-time Gmail login for a headless Pi: print the consent URL, let the user
# paste back the (unreachable) localhost redirect URL, and save token.json.
import os
from urllib.parse import parse_qs, urlparse

LOOPBACK_REDIRECT_URI = "http://localhost"


def authorization_code_from_callback(callback_url):
    codes = parse_qs(urlparse(callback_url.strip()).query).get("code")
    if not codes:
        raise ValueError("callback URL does not contain an authorization code")
    return codes[0]


def interactive_auth(credentials_path, token_path, scopes):
    if os.path.exists(token_path):
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
    with open(token_path, "w") as token_file:
        token_file.write(flow.credentials.to_json())
    os.chmod(token_path, 0o600)
    print("Gmail Authorization Successful!\n")
    return True
