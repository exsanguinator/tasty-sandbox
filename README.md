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

   `scan-put-bp.py` also needs a config file:
   ```bash
   cp margin-scan-config.json.example margin-scan-config.json
   # edit margin-scan-config.json with your account number and watchlist names
   ```
   `margin-scan-config.json` is gitignored since it holds your account number
   and watchlist names — only the `.example` file is checked in.

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
   TASTY_ENV=prod python scan-put-bp.py [config-path] [--csv|--html] [--debug]
   ```
   Reads `account_number` and `watchlists` from `margin-scan-config.json` (or the
   config path given as the first argument), resolves the equity tickers across
   those watchlists, filters out `.IVR` symbols, symbols with `liquidity-rating < 2`,
   and symbols without weekly options, then for each remaining ticker picks the
   nearest-to-45-DTE monthly expiration's nearest OTM put strike, dry-runs a
   1-lot sell-to-open order via `POST /accounts/{account_number}/orders/dry-run`,
   and writes the results ranked by `credit to bpr` (see column definitions below).
   Output is CSV to stdout by default, or `--csv` explicitly; pass `--html` to
   instead write a standalone HTML page with a click-to-sort results table. Pass
   `--debug` to print each ticker's raw `buying-power-effect` and any preflight
   errors to stderr.

   **Column definitions:**
   - `strike 52wk pct` — where the strike sits in the underlying's 52-week range:
     `(strike - 52wk_low) / (52wk_high - 52wk_low)`. `0.0` = strike at the 52-week
     low, `1.0` = at the 52-week high. Can fall slightly outside `[0, 1]` if the
     strike is beyond the current 52-week range.
   - `credit` — estimated premium received for selling 1 contract, in dollars
     (`option mid price * 100`).
   - `buying_power` — marginal buying-power/margin requirement this specific
     order would add to the account, from the order dry-run's isolated impact
     (`isolated-order-margin-requirement` / `change-in-buying-power`).
   - `credit to bpr` — `credit / buying_power`. **Capital efficiency under this
     account's margin rules**: how much premium you collect per dollar of buying
     power the trade actually consumes. The primary ranking column, since the
     whole point of this script is to find trades that use your account's
     margin (a scarce resource) efficiently — it is account- and margin-type
     -specific (Reg T vs. Portfolio Margin accounts will show very different
     numbers for the same trade).
   - `bpr to notional` — `buying_power / (strike * 100)`. What fraction of the
     trade's full notional (100 shares at the strike) your margin system is
     actually holding you to. Low values mean the account's margin treatment
     is very capital-efficient for that position (portfolio margin, existing
     offsetting positions, etc.); a value near `1.0` means you're being held to
     roughly cash-secured-put levels.
   - `credit to notional` — `credit / (strike * 100)`. A **reward** (yield)
     metric, not a risk or margin metric — the classic "cash-secured put
     yield": premium collected as a percentage of the capital you'd need if
     assigned. It's account- and margin-agnostic, so it's useful for comparing
     tickers on an apples-to-apples basis, but note it's an imperfect, indirect
     proxy for risk too: since premium scales with implied volatility, a high
     `credit to notional` often means the market is pricing in more risk for
     that name, not that you're being overpaid for the risk taken (i.e. it is
     not a measure of edge).

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
