import csv
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

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


def get_all_pages(path, **params):
    """Fetch all pages from a paginated endpoint, returning a flat list of items."""
    items = []
    params.setdefault("per-page", 250)
    page = 1
    while True:
        params["page-offset"] = (page - 1) * params["per-page"]
        data = get(path, **params)
        batch = data["data"].get("items", [])
        items.extend(batch)
        pagination = data.get("pagination") or data["data"].get("pagination", {})
        total = pagination.get("total-items", len(items))
        if len(items) >= total or not batch:
            break
        page += 1
    return items


def flatten(txn, account_number):
    row = {"account_number": account_number}
    for k, v in txn.items():
        if k == "lots":
            row[k] = json.dumps(v) if v is not None else ""
        else:
            row[k] = v
    return row


if __name__ == "__main__":
    start_time = (datetime.now(timezone.utc) - timedelta(days=7)).strftime(
        "%Y-%m-%dT%H:%M:%S%z"
    )

    accounts_resp = get("/customers/me/accounts")
    account_numbers = [
        item["account"]["account-number"]
        for item in accounts_resp["data"]["items"]
    ]
    print(f"Accounts found: {account_numbers}", file=sys.stderr)

    all_rows = []
    fieldnames_seen = []

    for acct in account_numbers:
        print(f"Fetching transactions for {acct}...", file=sys.stderr)
        txns = get_all_pages(
            f"/accounts/{acct}/transactions",
            **{"start-date": start_time},
        )
        print(f"  {len(txns)} transactions", file=sys.stderr)
        for txn in txns:
            row = flatten(txn, acct)
            for k in row:
                if k not in fieldnames_seen:
                    fieldnames_seen.append(k)
            all_rows.append(row)

    writer = csv.DictWriter(
        sys.stdout, fieldnames=fieldnames_seen, extrasaction="ignore"
    )
    writer.writeheader()
    writer.writerows(all_rows)
