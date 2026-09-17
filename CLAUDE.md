# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the script

```bash
source .venv/bin/activate
python explore.py
```

Switch environments via env var (defaults to `cert`):

```bash
TASTY_ENV=prod python explore.py
```

## Running transactions.py

Fetches all transactions from the last 7 days across all accounts and writes a CSV to stdout:

```bash
source .venv/bin/activate
python transactions.py > transactions.csv
```

```bash
TASTY_ENV=prod python transactions.py > transactions.csv
```

Progress and errors go to stderr; only the CSV goes to stdout.

## Architecture

### explore.py

Single-file script that authenticates against the Tastytrade API and exercises key endpoints.

### transactions.py

Fetches transactions for the last 7 days across all accounts under `GET /customers/me/accounts`, then paginates `GET /accounts/{acct}/transactions` for each. Outputs a CSV with `account_number` as the first column. The `lots` field is serialized as a JSON string if present. Column set is derived dynamically from whatever fields the API returns.

**Auth flow:** OAuth2 using a long-lived refresh token to obtain short-lived access tokens (15 min). `_ensure_token()` is called before every request and auto-refreshes when expired. On a 401 response, the token is force-refreshed and the request retried once. Credentials come from `.env` via `python-dotenv`.

**Required env vars:** `TASTY_CLIENT_SECRET`, `TASTY_REFRESH_TOKEN`, `TASTY_ENV` (`cert` or `prod`).

**Environment differences:**
- `cert` — `api.cert.tastyworks.com` — no market data endpoint
- `prod` — `api.tastyworks.com` — full access including `/market-data/by-type`
- Market data calls are gated behind `if _ENV == "prod"` to avoid 502s in cert
- Cert and prod require separate OAuth apps and grants (credentials are not shared)

**API conventions:**
- All requests require `Authorization: Bearer <token>` and `User-Agent: tasty-sandbox/1.0`
- Response bodies are JSON with a `data` envelope (e.g. `resp["data"]["items"]`)
- Quote endpoint is `/market-data/by-type` (not `/market-data/quotes`)
