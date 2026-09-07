import json
import os
import sys
import time

import requests
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

_ENV = os.environ.get("TASTY_ENV", "cert")
BASE_URLS = {
    "prod": "https://api.tastyworks.com",
    "cert": "https://api.cert.tastyworks.com",
}
if _ENV not in BASE_URLS:
    raise ValueError(f"Unknown TASTY_ENV '{_ENV}'. Choose from: {', '.join(BASE_URLS)}")
BASE_URL = BASE_URLS[_ENV]
USER_AGENT = "tasty-sandbox/1.0"

print(f"Environment: {_ENV} ({BASE_URL})", file=sys.stderr)

_access_token = None
_token_expires_at = 0


def _fetch_access_token():
    global _access_token, _token_expires_at
    resp = requests.post(
        f"{BASE_URL}/oauth/token",
        headers={"User-Agent": USER_AGENT},
        data={
            "grant_type": "refresh_token",
            "refresh_token": os.environ["TASTY_REFRESH_TOKEN"],
            "client_secret": os.environ["TASTY_CLIENT_SECRET"],
        },
    )
    if not resp.ok:
        raise RuntimeError(f"Token request failed {resp.status_code}: {resp.text}")
    payload = resp.json()
    _access_token = payload["access_token"]
    _token_expires_at = time.time() + payload["expires_in"] - 30
    print("Access token refreshed.", file=sys.stderr)


def _ensure_token():
    if not _access_token or time.time() >= _token_expires_at:
        _fetch_access_token()


def _headers():
    return {
        "Authorization": f"Bearer {_access_token}",
        "User-Agent": USER_AGENT,
    }


def get(path, **params):
    _ensure_token()
    r = requests.get(f"{BASE_URL}{path}", headers=_headers(), params=params)
    if r.status_code == 401:
        _fetch_access_token()
        r = requests.get(f"{BASE_URL}{path}", headers=_headers(), params=params)
    if not r.ok:
        print(f"  URL: {r.url}", file=sys.stderr)
        print(f"  Status: {r.status_code}", file=sys.stderr)
        print(f"  Response: {r.text}", file=sys.stderr)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    print("Fetching watchlists...", file=sys.stderr)
    resp = get("/watchlists")
    print(json.dumps(resp, indent=2))
