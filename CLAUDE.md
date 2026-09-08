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

## Running scan-put-bp.py

Ranks short-put candidates from configured watchlists by credit-to-buying-power efficiency. Requires `TASTY_ENV=prod` (uses `/market-data/by-type`) and an OAuth grant with the `trade` scope (it dry-runs orders):

```bash
source .venv/bin/activate
TASTY_ENV=prod python scan-put-bp.py [config-path] [--csv|--html] [--debug]
```

Reads `account_number` and `watchlists` from `margin-scan-config.json` (or the config path given as the first argument). Output is CSV to stdout by default; `--html` writes a standalone sortable HTML table instead. See README.md for full column definitions.

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

### scan-put-bp.py

Resolves equity tickers from configured watchlists, filters out `.IVR` symbols, symbols with `liquidity-rating < 2` (via `/market-metrics`, which also supplies the `ivr`/`ivx` columns), and symbols without weekly options. For each remaining ticker, picks the nearest-to-45-DTE monthly expiration's nearest OTM put strike, dry-runs a 1-lot sell-to-open order via `POST /accounts/{account_number}/orders/dry-run` to get the marginal buying-power impact, and ranks results by `credit to bpr` (see README.md for column definitions). `credit to bpr`, `bpr to notional`, `credit to notional`, `ivr`, and `ivx` are all output as zero-padded percentages (e.g. `"1.10"`), not raw fractions.

Same auth flow, env vars, and API conventions as above. Unlike `explore.py`, this script hard-requires `TASTY_ENV=prod` and exits early otherwise, since it depends on `/market-data/by-type` for underlying/option prices.
