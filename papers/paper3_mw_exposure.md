# Paper 3 — Minimum-wage exposure alignment

Reproduced via public MW sources plus the eighty6 QCEW API; see `scripts/03_build_mw.py` and `scripts/04_reproduce.py`. Covers **RQ6**. **No outcome regressions.**

## Why the API is not enough

`GET /v1/qcew/employment` does not serve statutory minimum wages. Exposure is rebuilt from the same public sources the study used:

| Source | Role | URL | Retrieved |
|--------|------|-----|-----------|
| Vaghul–Zipperer historicalminwage v1.4.0 | State-quarter rates through 2022Q4 | https://github.com/benzipperer/historicalminwage/releases/tag/v1.4.0 | 2026-08-16 |
| DOL WHD history + mid-year rebuild | 2023–2026 applicable rates | https://www.dol.gov/agencies/whd/state/minimum-wage/history | 2026-08-16 |
| BLS CPI-U (CUUR0000SA0) | Real 2024 USD | https://www.bls.gov/cpi/ | 2026-08-16 |
| Berkeley Labor Center inventory | Local-ordinance **flag** (26 counties) | https://laborcenter.berkeley.edu/inventory-of-us-city-and-county-minimum-wage-ordinances/ | 2026-08-16 |

Applicable rate = max($7.25 federal, state basic). State is `area_fips[:2]`. Kaitz_7225 = MW / (AWW_7225 / 40).

## Headline findings

- MW panel: **10,761** state-quarters (1974–2026 when VZ is present).
- Merge onto 2014–2025 county-quarters: **97.553%** (3,811 misses).
- 2024Q1 applicable MW ranges **$7.25–$17.00** in the deliverable snapshot.
- Restaurant Kaitz median **0.993**, P90 **1.435** — the statutory floor is close to implied hourly AWW in many counties.
- Florida 2023 rebuild: Q1–Q3 = **$11**, Q4 = **$12** (Amendment 2 September 30 step).
- Local-ordinance flag: **26** counties (0.812% of 3,201). This is a misalignment flag, not a population-weighted city rate.

## Caveats

NY/OR intra-state tiers are not captured. Tipped cash-wage exposure is a flag only. Do not construct “MW rank” as a treatment.
