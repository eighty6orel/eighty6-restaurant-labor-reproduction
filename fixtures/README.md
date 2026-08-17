# Fixtures

These files are a **tiny, public-safe** QCEW-shaped sample so clones and CI can run without an API key.

| File | What it is |
|------|------------|
| `qcew_national_sample.json` | U.S. national private series (`area_fips=US000`) for a handful of quarters |
| `qcew_county_sample.json` | Eight counties × eight quarters, study industries only |
| `mw_sample.json` | State-quarter statutory rates covering the fixture geographies |

They are **illustrative**. Identities (shares in (0, 1), wage share = restaurant wages / all-industry wages) are real. Paper-grade county counts, correlations, TWFE coefficients, and event-study paths require a live **Pro** pull of the full county universe.

Do not treat fixture headlines as the study findings. Canonical numbers live in `expected/headlines.json`.
