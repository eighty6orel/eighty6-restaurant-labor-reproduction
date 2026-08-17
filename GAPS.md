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

Committed samples have eight counties and eight quarters. Offline RQ1 county n will be 8, not 2,538. Do not cite fixture output as study results.

## What this repo will not do

- It will not connect to Postgres or ship a `research_area_panel` dump.
- It will not upgrade RQ7–RQ10 to causal language.
- It will not make the private platform monorepo public.
