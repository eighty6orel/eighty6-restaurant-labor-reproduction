# Residual gaps

Honest limits of this companion. Nothing here is a new finding.

## Live API not run in CI

GitHub Actions has no `E86_API_KEY`. CI proves identities on fixtures. Paper-grade headline comparison (`expected/headlines.json` tolerances) is a **local** live Pro run:

```text
python scripts/01_pull_qcew.py --geography all
python scripts/03_build_mw.py
python scripts/04_reproduce.py --live
```

If this environment has no key, the live path is documented but not executed here.

## `api.eighty6data.com`

On 2026-08-17, `GET https://www.eighty6data.com/api/health` returned `{"status":"healthy"}`. `https://api.eighty6data.com/health` did not. This package defaults to `https://www.eighty6data.com/api`.

## Single-code filters

Production `GET /v1/qcew/employment` accepts one `industry_code` and one `agglvl_code` per request (OpenAPI 2026-08-17). The client loops. That is slower than a multi-code filter would be; it is not a blocker.

## Vaghul–Zipperer workbook

The quarterly Excel file is downloaded at runtime from the public v1.4.0 zip. It is not committed (752 KB zip; not a QCEW dump, but still a binary). If the download fails, `scripts/03_build_mw.py` falls back to DOL rates from 2020 and records the source as `dol_whd_fallback_pre2023`. RQ6 panel row counts that assume VZ back to 1974 will then differ; 2014–2025 inference still has statutory rates.

## Callaway–Sant’Anna optional extra

RQ8 uses `csdid` when installed (`pip install -e ".[eventstudy]"`). Without it, the script records `cs_ok=false` and keeps `cs_causal=false` (the deliverable already failed the causal screen). The stacked `pyfixest` robustness path is also in that extra.

## RQ9 adjacency

Census `county_adjacency.txt` is fetched over HTTPS on live RQ9 runs and gitignored. Offline `--offline` skips the download so first-time clones stay network-light; RQ9 then records an adjacency gap. Live runs need the Census file — the same URL the study used.

## Fixture headlines ≠ paper headlines

Committed samples have eight counties and eight quarters. National fixture employment and wage shares are **illustrative** (they do not equal the RQ5 job counts or RQ1 paper shares). Offline RQ1 county n will be 8, not 2,538. Do not cite fixture output as study results.

## TWFE on fixtures

`linearmodels.PanelOLS` needs ≥ 80 complete rows. The eight-county fixture is below that threshold, so offline RQ7/RQ10 return `error: too few rows`. That is expected. Live Pro panels reproduce the deliverable coefficients.

## RQ8 pre-trend cells

The deliverable reports CS ATT at e=−8, e=−4, e=0, e=+3 and stacked `rel::0`. Those paths require `csdid` plus the full state-year panel. This package implements the same estimator; without `csdid` or a live panel the terms are absent and `cs_causal` stays false (matching the locked screen).

## City generation is a geography rebuild

`generations/20260818-citygen/` publishes the county→CBSA crosswalk and the sum-then-divide identity. It does **not** ship city-level RQ estimators. After `scripts/02_build_panel.py`, run `python generations/20260818-citygen/src/aggregate_to_cities.py`. Compare city figures only to that generation, never to `papers/rq/`.

## Hygiene audits

- **2026-08-17 (Loops C–D):** tracked tree has no parquet, pptx, `.env`, or PDFs. History on `main` contains no live `e86_` keys. Client params match production OpenAPI. Papers do not claim causation for RQ7–RQ10.
- **2026-08-20:** Dependabot weekly PRs disabled (pinned deps are part of the lock). Public tree no longer lists private Drive paths, platform-repo branches, local Windows paths, or unused election/tax fields.

## What this repo will not do

- It will not connect to Postgres or ship a research-panel dump.
- It will not upgrade RQ7–RQ10 to causal language.
- It will not publish internal research-process notes.
