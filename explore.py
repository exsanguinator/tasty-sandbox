import os
import json
import time
import requests
from dotenv import load_dotenv, find_dotenv

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

print(f"Environment: {_ENV} ({BASE_URL})")

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
        }
    )
    if not resp.ok:
        raise RuntimeError(f"Token request failed {resp.status_code}: {resp.text}")
    payload = resp.json()
    _access_token = payload["access_token"]
    _token_expires_at = time.time() + payload["expires_in"] - 30  # 30s buffer
    print("Access token refreshed.\n")


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
        print(f"  URL: {r.url}")
        print(f"  Status: {r.status_code}")
        print(f"  Response: {r.text}")
    r.raise_for_status()
    return r.json()


def pp(data):
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    _ensure_token()

    print("=== Customer Info ===")
    pp(get("/customers/me"))

    print("\n=== Accounts ===")
    accounts = get("/customers/me/accounts")
    pp(accounts)

    account_number = accounts["data"]["items"][0]["account"]["account-number"]
    print(f"\nUsing account: {account_number}")

    print("\n=== Balances ===")
    pp(get(f"/accounts/{account_number}/balances"))

    print("\n=== Positions ===")
    pp(get(f"/accounts/{account_number}/positions"))

    if _ENV == "prod":
        print("\n=== Quote: AAPL,NVDA ===")
        pp(get("/market-data/by-type", equity="AAPL,NVDA"))

        print("\n=== Metrics: AAPL,NVDA ===")
        pp(get("/market-metrics", symbols="AAPL,NVDA"))
    else:
        print("\n(Skipping market data and metrics — not available outside prod)")

    print("\n=== Option Chain: AAPL ===")
    pp(get("/option-chains/AAPL/nested"))
    
