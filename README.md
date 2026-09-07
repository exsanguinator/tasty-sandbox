# Tastytrade API Sandbox

A Python script for learning and exploring the Tastytrade API.

## Environments

| `TASTY_ENV` | Base URL | Market Data | Option Chains |
|---|---|---|---|
| `cert` (default) | api.cert.tastyworks.com | No | Yes |
| `prod` | api.tastyworks.com | Yes | Yes |

## Setup

1. **Create an OAuth application** 

   - in `cert` on [developer.tastytrade.com](https://developer.tastytrade.com/sandbox/)
      - Sign-in with your developer credentials
      - under the section `OAuth2 in Sandbox`, Create an Account
      - under the section `OAuth2 Application`, Create Grant
      - save the `Client Secret` and `Refresh Token`

   - in `prod` on [my.tastytrade.com](https://my.tastytrade.com)
      - Manage tab > My Profile > API > OAuth Applications > + New OAuth client
      - Save your `Client Secret` — shown only once

      - **Generate a personal grant**
         - On the same page, click `"..."` > Create Grant
         - Save the `Refresh Token` — this never expires

2. **Create a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install requests python-dotenv
   ```

4. **Configure credentials**
   ```bash
   cp .env.example .env
   # edit .env with your environment, client secret, and refresh token
   ```

5. **Run**

   Explore API endpoints:
   ```bash
   python explore.py
   ```

   Export last 7 days of transactions to CSV:
   ```bash
   python transactions.py > transactions.csv
   ```

   Dump all watchlists:
   ```bash
   python get-watchlists.py
   ```

   Dump margin requirements for every account:
   ```bash
   python get-margin-req.py
   ```

   Rank short-put candidates from your watchlists by credit-to-buying-power efficiency
   (requires `TASTY_ENV=prod` and an OAuth grant with the `trade` scope):
   ```bash
   TASTY_ENV=prod python scan-put-bp.py [config-path] [--debug]
   ```
   Reads `account_number` and `watchlists` from `margin-scan-config.json` (or the
   config path given as the first argument), resolves the equity tickers across
   those watchlists, filters out `.IVR` symbols, symbols with `liquidity-rating < 2`,
   and symbols without weekly options, then for each remaining ticker picks the
   nearest-to-45-DTE monthly expiration's nearest OTM put strike, dry-runs a
   1-lot sell-to-open order via `POST /accounts/{account_number}/orders/dry-run`,
   and writes a CSV to stdout ranked by `credit / buying_power`. Pass `--debug` to
   print each ticker's raw `buying-power-effect` and any preflight errors to stderr.

   As a notebook:
   ```bash
   pip install jupyter
   jupyter notebook explore.ipynb
   ```

To deactivate the virtual environment when done: `deactivate`

## Notes

- Access tokens expire after 15 minutes and are refreshed automatically
- Market data (`/market-data/by-type`) is only available in `prod`
- Cert credentials and prod credentials are separate — each environment needs its own OAuth app and grant
- `scan-put-bp.py` places dry-run orders, which requires the OAuth grant's refresh token to include the `trade` scope in addition to `read` — regenerate the grant after adding the scope, since existing refresh tokens aren't upgraded retroactively
