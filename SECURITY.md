# Security

## Reporting a vulnerability

Email **security@eighty6data.com** or open a private GitHub security advisory on this repository.

Do **not** file a public issue that contains credentials.

## API keys

Reproduction against the live eighty6 API uses a Bearer token created in the [dashboard](https://www.eighty6data.com).

- Keys look like `e86_…`
- Store them in a local `.env` (gitignored) or your shell environment
- Never commit `.env`, paste a key into an issue, or embed a key in a notebook
- If a key leaks, revoke it in the dashboard and create a new one

This repository never needs `DATABASE_URL`, Stripe secrets, or JWT signing keys. Those belong to the API operator, not to API clients.

## What this repo stores

Committed fixtures are tiny, public-safe QCEW-shaped samples. Live pulls land in `data/` and are gitignored.
