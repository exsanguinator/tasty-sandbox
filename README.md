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
