#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import json
import sys
import os
import hashlib
import base64
import secrets
import time
import logging
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
import requests

from accounts import account_file, account_from_argv

# --- Configuration ---
SCRIPT_DIR = Path(__file__).parent.resolve()
LOG_FILE = SCRIPT_DIR / "claude_monitor.log"

CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e" # Public
AUTHORIZE_URL = "https://claude.ai/oauth/authorize"
TOKEN_URL = "https://platform.claude.com/v1/oauth/token"
USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
REDIRECT_URI = "http://localhost:18924/callback"
SCOPES = "user:inference user:profile"
REFRESH_BUFFER_SEC = 600
USER_AGENT = "claude-code/2.0.32"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClaudeAccountFiles:
    credentials: Path
    usage: Path


def account_files(account: str) -> ClaudeAccountFiles:
    return ClaudeAccountFiles(
        credentials=account_file("claude_creds", account),
        usage=account_file("claude_usage", account),
    )


def generate_pkce():
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def generate_state():
    return secrets.token_urlsafe(32)


def load_credentials(files: ClaudeAccountFiles) -> dict | None:
    if files.credentials.exists():
        try:
            return json.loads(files.credentials.read_text())
        except (json.JSONDecodeError, OSError):
            return None
    return None


def save_credentials(creds: dict, files: ClaudeAccountFiles):
    files.credentials.write_text(json.dumps(creds, indent=2))
    os.chmod(files.credentials, 0o600)


def token_is_expired(creds: dict) -> bool:
    expires_at = creds.get("expiresAt", 0)
    now_ms = int(time.time() * 1000)
    return now_ms >= (expires_at - REFRESH_BUFFER_SEC * 1000)


def interactive_auth(account: str) -> bool:
    """Interactive authorization flow for the main script setup."""
    files = account_files(account)
    if load_credentials(files):
        return True

    verifier, challenge = generate_pkce()
    state = generate_state()

    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    auth_url = AUTHORIZE_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items())

    print("\n" + "=" * 60)
    print(f"  CLAUDE AI AUTHORIZATION REQUIRED (account: {account})")
    print("=" * 60)
    print("\n1. Open this URL in any browser:\n")
    print(f"   {auth_url}\n")
    print(f"2. Log in with the Claude account for '{account}'.")
    print("3. After login, copy the FULL URL from the browser address bar.")
    print("   (It will look like http://localhost:18924/callback?code=...&state=...)\n")

    callback_url = input("Paste the full callback URL here (or press Enter to disable): ").strip()

    if not callback_url:
        print("Authorization cancelled. Claude widget is disabled.\n")
        return False

    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(callback_url)
    qs = parse_qs(parsed.query)

    code = None
    if "code" in qs:
        code = qs["code"][0]
    elif parsed.fragment:
        parts = parsed.fragment.split("#")
        if parts:
            code = parts[0]

    if not code:
        print("Could not extract authorization code from the URL. Disabling Claude.")
        return False

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": verifier,
        "state": state,
    }

    try:
        resp = requests.post(TOKEN_URL, json=payload, timeout=15)
        if resp.status_code != 200:
            print(f"Token exchange failed: {resp.status_code} {resp.text}")
            return False

        data = resp.json()
        creds = {
            "accessToken": data.get("access_token"),
            "refreshToken": data.get("refresh_token"),
            "expiresAt": int(time.time() * 1000) + data.get("expires_in", 28800) * 1000,
            "scopes": data.get("scope", SCOPES).split(),
        }

        save_credentials(creds, files)
        print(f"Claude Authorization Successful for '{account}'!\n")
        return True
    except Exception as e:
        print(f"Failed to fetch Claude tokens: {e}")
        return False


def refresh_access_token(creds: dict, files: ClaudeAccountFiles) -> dict | None:
    refresh_token = creds.get("refreshToken") or creds.get("refresh_token")
    if not refresh_token:
        log.error("No refresh token found in credentials.")
        return None

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
    }
    try:
        resp = requests.post(TOKEN_URL, json=payload, timeout=15)
        if resp.status_code != 200:
            log.error(f"Token refresh failed: {resp.status_code} {resp.text}")
            return None
        data = resp.json()
        creds["accessToken"] = data.get("access_token")
        creds["expiresAt"] = int(time.time() * 1000) + data.get("expires_in", 28800) * 1000
        if "refresh_token" in data:
            creds["refreshToken"] = data["refresh_token"]
        save_credentials(creds, files)
        return creds
    except requests.RequestException as e:
        log.error(f"Network error during refresh: {e}")
        return None


def fetch_usage(access_token: str) -> dict | None:
    if not access_token:
        return None

    headers = {
        "Authorization": f"Bearer {access_token}",
        "anthropic-beta": "oauth-2025-04-20",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    try:
        resp = requests.get(USAGE_URL, headers=headers, timeout=15)
        if resp.status_code in [401, 429]:
            log.warning(f"Usage request returned {resp.status_code}")
            return None
        if resp.status_code != 200:
            log.error(f"Usage request failed: {resp.status_code} {resp.text}")
            return None
        return resp.json()
    except requests.RequestException as e:
        log.error(f"Network error fetching usage: {e}")
        return None


def save_usage(raw: dict, files: ClaudeAccountFiles):
    five = raw.get("five_hour")
    seven = raw.get("seven_day")
    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "five_hour": {
            "utilization": five.get("utilization", 0) if five else 0,
            "resets_at": five.get("resets_at") if five else None,
        },
        "seven_day": {
            "utilization": seven.get("utilization", 0) if seven else 0,
            "resets_at": seven.get("resets_at") if seven else None,
        },
    }
    files.usage.write_text(json.dumps(output, indent=2))


def save_usage_error(reason: str, files: ClaudeAccountFiles):
    files.usage.write_text(json.dumps({"error": reason}, indent=2))


def main():
    files = account_files(account_from_argv(sys.argv))
    creds = load_credentials(files)
    if not creds:
        log.error("No credentials. Run main script to authenticate first.")
        sys.exit(1)

    if token_is_expired(creds):
        creds = refresh_access_token(creds, files)
        if not creds:
            save_usage_error("token_refresh_failed", files)
            sys.exit(1)

    raw = fetch_usage(creds.get("accessToken"))
    if raw is None:
        creds = refresh_access_token(creds, files)
        if creds:
            raw = fetch_usage(creds.get("accessToken"))

    if raw:
        save_usage(raw, files)
    else:
        save_usage_error("fetch_failed", files)


if __name__ == "__main__":
    main()