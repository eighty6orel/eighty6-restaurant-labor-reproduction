# Reproduce the restaurant labor papers from the eighty6 QCEW API

This repository is a **public companion** to the Wage Share Restaurant Health papers (RQ1–RQ10). It is an API client, not a data dump. You create a key at [eighty6data.com](https://www.eighty6data.com), pull the same BLS QCEW slice the papers used, rebuild minimum-wage exposure from cited public sources, and regenerate the headline tables and figures.

```bash
pip install -e ".[dev]"
python scripts/04_reproduce.py --offline
```

That offline command needs no key. It runs the estimators on a tiny committed sample so you can see the pipeline. Paper-grade county results need a live **Pro** pull — Basic cannot page the full county universe in a reasonable number of 1,000-row, 365-day requests.

## What you can reproduce

| ID | Finding | Tier |
|----|---------|------|
| RQ1 | U.S. 7225 wage-bill share 2.4534% (2014Q1) → 2.7005% (2024Q1); 2,538 counties; 90.8% of variance is between counties | Descriptive |
| RQ2 | Within-county 4q Δepe–ΔAWW correlations: 7225 −0.022, FSR +0.051, LSR −0.129 | Association |
| RQ3 | Cronbach’s α = 0.615; two PCA components — a one-number “health” index is not supported | Measurement |
| RQ4 | Equal-weight vs PC1 rank Spearman 0.941; median bootstrap rank width 432 | Descriptive / measurement |
| RQ5 | FSR employment −48.6% in 2020Q2 vs 2019Q4; LSR/other −17.2% | Descriptive |
| RQ6 | MW merge rate 97.6%; 2024Q1 Kaitz median 0.993 | Measurement |
| RQ7 | TWFE ln real MW → ln emp −0.049 (SE 0.046) — **conditional association, not an effect** | Association |
| RQ8 | CS event study around ≥10% real MW jumps; pre-trends fail; no causal verbs | Design-based (failed screen) |
| RQ9 | Border-county FD correlation −0.036 | Design-based association |
| RQ10 | FSR/LSR split-sample TWFE; still association | Association |

Canonical numbers and tolerances: [`expected/headlines.json`](expected/headlines.json). Papers: [`papers/README.md`](papers/README.md).

**City layer (generation `citygen-20260818`).** After a live county panel, rebuild the 100 largest CBSAs with [`generations/20260818-citygen/`](generations/20260818-citygen/). City shares are summed numerators over summed denominators — never an average of county shares. Do not mix those figures with `papers/rq/` county numbers.

## Get an API key

1. Create an account at [https://www.eighty6data.com](https://www.eighty6data.com).
2. Open the dashboard and create an API key. It starts with `e86_`.
3. Choose a plan:
   - **Basic** — 60 requests/min, 1,000 rows/request, 365-day range. Enough for the national series and a small county sample.
   - **Pro** — 300 requests/min, 10,000 rows/request, 3,650-day range. This is the honest path for the full county panel (RQ1 county quantiles, RQ2–RQ4, RQ7–RQ10).

Never commit the key. Revoke it in the dashboard if it leaks.

## Install

Python 3.11 or newer.

```bash
git clone https://github.com/eighty6orel/eighty6-restaurant-labor-reproduction.git
cd eighty6-restaurant-labor-reproduction
python -m venv .venv
```

**PowerShell**

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

If you prefer to activate the venv and `Activate.ps1` is blocked, run
`Set-ExecutionPolicy -Scope Process RemoteSigned` once in that window, or keep
calling `.venv\Scripts\python.exe` and `.venv\Scripts\pip.exe` directly.

**bash**

```bash
source .venv/bin/activate
pip install -e ".[dev]"
```

## Configure

```bash
cp .env.example .env
```

PowerShell: `Copy-Item .env.example .env`

Edit `.env`:

```text
E86_API_KEY=e86_your_key_here
E86_API_BASE=https://www.eighty6data.com/api
E86_PLAN=pro
```

`E86_API_BASE` is the working production proxy (verified `GET /health` → `{"status":"healthy"}` on 2026-08-17). OpenAPI: [https://www.eighty6data.com/api/docs](https://www.eighty6data.com/api/docs).

## Two ways to run

### Offline fixture demo (no key)

```bash
pytest
python scripts/04_reproduce.py --offline
```

Fixtures are eight counties and a U.S. national path. They prove identities (shares in (0, 1), wage share = restaurant wages / all-industry wages). They are **not** the paper numbers.

### Live API reproduce (key required)

```bash
python scripts/00_check_api.py
python scripts/01_pull_qcew.py --geography national
python scripts/03_build_mw.py
python scripts/02_build_panel.py
python scripts/04_reproduce.py --live
```

Full county panel (Pro):

```bash
python scripts/01_pull_qcew.py --geography all --start-year 2014 --end-year 2025
python scripts/03_build_mw.py
python scripts/02_build_panel.py
python scripts/04_reproduce.py --live
python scripts/05_compare_headlines.py
```

National RQ1/RQ5 headlines can be checked on Basic. County quantiles, TWFE, event study, and border pairs need Pro. Offline comparison (`python scripts/05_compare_headlines.py --offline`) skips county-only headlines.

## Command sequence

**PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\pytest.exe
.\.venv\Scripts\python.exe scripts/04_reproduce.py --offline
```

**bash**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
python scripts/04_reproduce.py --offline
```

## How the API maps to the study

| Paper construct | QCEW fields | Query params |
|-----------------|-------------|--------------|
| Private all-industry wage bill / employment | `total_qtrly_wages`, `annual_avg_emplvl` | `industry_code=10`, `ownership_code=5`, `size_code=0`, `agglvl_code=71` (county) / `11` (US) |
| Restaurant 4-digit | same | `industry_code=7225`, `agglvl_code=76` / `16` |
| Full-service | same | `industry_code=722511`, `agglvl_code=78` / `18` |
| Limited-service / other | same, summed | `722513`, `722514`, `722515` at 6-digit agglvl |
| Disclosure | `disclosure_code` | Drop `'N'` and null wages/employment in the client |
| Time window | `year`, `qtr` | `year=` or `start_year` + `end_year` (plan-capped) |
| Pagination | — | `limit`, `offset`; response `total`, `has_more` |

The API accepts **one** `industry_code` and **one** `agglvl_code` per request. The client loops and paginates. Statutory minimum wages are **not** in this endpoint — `scripts/03_build_mw.py` rebuilds them.

## Plan limits and expected runtime

| Plan | rpm | max rows / request | max date range | Honest use |
|------|-----|--------------------|----------------|------------|
| Basic | 60 | 1,000 | 365 days | National series; small county sample |
| Pro | 300 | 10,000 | 3,650 days | Full county-year panel |

A full 2014–2025 county pull loops ~13 industries × 3 county agglvls × year chunks, then pages at 10,000 rows. Budget on the order of **hundreds of requests** and **10–40 minutes** on Pro, longer on Basic (1,000-row pages and one-year chunks). The client sleeps on `429` using `Retry-After`.

## Inference discipline

- RQ1 and RQ5 are **descriptive**.
- RQ2, RQ7, and RQ10 are **associations** (first differences or two-way FE). Do not write “the effect of the minimum wage.”
- RQ3, RQ4, and RQ6 are **measurement**.
- RQ8 is a design-based **candidate**. Pre-trends fail; `causal_reading` is false. RQ9 and RQ10 inherit that gate.

## Data provenance and licenses

- **BLS QCEW** is public statistical data. This package accesses it through a paid eighty6 API ([terms on eighty6data.com](https://www.eighty6data.com)).
- **Vaghul and Zipperer (2022)**, historicalminwage v1.4.0, [GitHub release](https://github.com/benzipperer/historicalminwage/releases/tag/v1.4.0).
- **U.S. DOL WHD** state minimum-wage history, [DOL table](https://www.dol.gov/agencies/whd/state/minimum-wage/history), transcribed 2026-08-16.
- **Census** county adjacency, [county_adjacency.txt](https://www2.census.gov/geo/docs/reference/county_adjacency.txt).
- **Census** Vintage 2024 CBSA population and OMB Bulletin 23-01 delineations (city generation only). URLs in `generations/20260818-citygen/data/crosswalk_meta.json`.
- This repository is **MIT** (see `LICENSE`).

## Citing this repo and the papers

```text
Eighty6. 2026. eighty6 restaurant labor reproduction (Version 0.1.0).
https://github.com/eighty6orel/eighty6-restaurant-labor-reproduction
```

Also cite BLS QCEW and Vaghul–Zipperer v1.4.0. Machine-readable metadata: `CITATION.cff`. Paper text: `papers/`.

## Security

See [SECURITY.md](SECURITY.md). Never paste an `e86_` key into an issue or pull request.
