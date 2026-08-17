# Contributing

This repository is a **client** of the [eighty6 QCEW API](https://www.eighty6data.com). It reconstructs the restaurant labor papers; it is not the API itself.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix:    source .venv/bin/activate
pip install -e ".[dev]"
```

## Checks before a PR

```bash
ruff check src scripts tests
pytest
python scripts/04_reproduce.py --offline
```

Do not run live API pulls in CI. Do not commit `.env`, parquet extracts, or API keys.

## Scope

- Bug fixes in the client, panel identities, MW rebuild, or documentation are welcome.
- Do not add a path that reads Postgres or a private research dump.
- Do not upgrade inference language. RQ7 is a conditional association. RQ8–RQ10 do not support causal verbs (pre-trends failed).
- Headline numbers in `expected/headlines.json` come from the published RQ deliverables. Change them only with a citation.

## Pull requests

Use the PR template. Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`) keep history readable. Never paste an `e86_` key into the PR body.
