"""Rebuild state × quarter minimum-wage exposure from public sources.

The eighty6 QCEW API does not serve statutory minimum wages. This module
rebuilds the same panel the papers used:

- Vaghul–Zipperer historicalminwage v1.4.0 through 2022Q4
  (https://github.com/benzipperer/historicalminwage/releases/tag/v1.4.0)
- DOL WHD state basic rates for 2023–2026, transcribed from
  https://www.dol.gov/agencies/whd/state/minimum-wage/history
  (retrieved 2026-08-16 in the original study)
- CPI-U annual averages, BLS CUUR0000SA0, base year 2024
- Local-ordinance county flag from the Berkeley Labor Center inventory
  (misalignment flag, not a population-weighted city rate)

Applicable rate = max(federal $7.25, state basic).
"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import date
from pathlib import Path
from urllib.request import urlopen

import polars as pl

from eighty6_repro.config import (
    BERKELEY_LOCAL_URL,
    CPI_BASE_YEAR,
    DOL_CONS_URL,
    DOL_HIST_URL,
    DOL_STATE_URL,
    FEDERAL_MW,
    STATE_FIPS_NAMES,
    VZ_RELEASE_URL,
)
from eighty6_repro.paths import extracts_dir, fixtures_dir, raw_dir

RETRIEVED = date(2026, 8, 16)
VZ_ZIP_URL = (
    "https://github.com/benzipperer/historicalminwage/releases/download/v1.4.0/mw_state_excel.zip"
)

# DOL Jan-1 basic rates. "..." states coded as 0 then floored at federal.
# Transcribed from DOL WHD history table (revised January 2025), retrieved 2026-08-16.
DOL_JAN1: dict[str, dict[int, float]] = {
    "01": {2020: 0, 2021: 0, 2022: 0, 2023: 0, 2024: 0, 2025: 0, 2026: 0},
    "02": {2020: 10.19, 2021: 10.34, 2022: 10.34, 2023: 10.85, 2024: 11.73, 2025: 11.91, 2026: 13.00},
    "04": {2020: 12.00, 2021: 12.15, 2022: 12.80, 2023: 13.85, 2024: 14.35, 2025: 14.70, 2026: 15.15},
    "05": {2020: 10.00, 2021: 11.00, 2022: 11.00, 2023: 11.00, 2024: 11.00, 2025: 11.00, 2026: 11.00},
    "06": {2020: 12.00, 2021: 13.00, 2022: 14.00, 2023: 15.50, 2024: 16.00, 2025: 16.50, 2026: 16.90},
    "08": {2020: 12.02, 2021: 12.32, 2022: 12.56, 2023: 13.65, 2024: 14.42, 2025: 14.81, 2026: 15.16},
    "09": {2020: 12.00, 2021: 13.00, 2022: 14.00, 2023: 15.00, 2024: 15.69, 2025: 16.35, 2026: 16.94},
    "10": {2020: 9.25, 2021: 9.25, 2022: 10.50, 2023: 11.75, 2024: 13.25, 2025: 15.00, 2026: 15.00},
    "11": {2020: 15.00, 2021: 15.20, 2022: 16.10, 2023: 17.00, 2024: 17.50, 2025: 17.50, 2026: 17.95},
    "12": {2020: 8.56, 2021: 10.00, 2022: 10.00, 2023: 12.00, 2024: 12.00, 2025: 13.00, 2026: 14.00},
    "13": {2020: 5.15, 2021: 5.15, 2022: 5.15, 2023: 5.15, 2024: 5.15, 2025: 5.15, 2026: 5.15},
    "15": {2020: 10.10, 2021: 10.10, 2022: 12.00, 2023: 12.00, 2024: 14.00, 2025: 14.00, 2026: 16.00},
    "16": {2020: 7.25, 2021: 7.25, 2022: 7.25, 2023: 7.25, 2024: 7.25, 2025: 7.25, 2026: 7.25},
    "17": {2020: 10.00, 2021: 11.00, 2022: 12.00, 2023: 13.00, 2024: 14.00, 2025: 15.00, 2026: 15.00},
    "18": {2020: 7.25, 2021: 7.25, 2022: 7.25, 2023: 7.25, 2024: 7.25, 2025: 7.25, 2026: 7.25},
    "19": {2020: 7.25, 2021: 7.25, 2022: 7.25, 2023: 7.25, 2024: 7.25, 2025: 7.25, 2026: 7.25},
    "20": {2020: 7.25, 2021: 7.25, 2022: 7.25, 2023: 7.25, 2024: 7.25, 2025: 7.25, 2026: 7.25},
    "21": {2020: 7.25, 2021: 7.25, 2022: 7.25, 2023: 7.25, 2024: 7.25, 2025: 7.25, 2026: 7.25},
    "22": {2020: 0, 2021: 0, 2022: 0, 2023: 0, 2024: 0, 2025: 0, 2026: 0},
    "23": {2020: 12.00, 2021: 12.15, 2022: 12.75, 2023: 13.80, 2024: 14.15, 2025: 14.65, 2026: 15.10},
    "24": {2020: 11.00, 2021: 11.75, 2022: 12.50, 2023: 13.25, 2024: 15.00, 2025: 15.00, 2026: 15.00},
    "25": {2020: 12.75, 2021: 13.50, 2022: 14.25, 2023: 15.00, 2024: 15.00, 2025: 15.00, 2026: 15.00},
    "26": {2020: 9.65, 2021: 9.65, 2022: 9.87, 2023: 10.10, 2024: 10.33, 2025: 12.48, 2026: 13.73},
    "27": {2020: 10.00, 2021: 10.08, 2022: 10.33, 2023: 10.59, 2024: 10.85, 2025: 11.13, 2026: 11.41},
    "28": {2020: 0, 2021: 0, 2022: 0, 2023: 0, 2024: 0, 2025: 0, 2026: 0},
    "29": {2020: 9.45, 2021: 10.30, 2022: 11.15, 2023: 12.00, 2024: 12.30, 2025: 13.75, 2026: 15.00},
    "30": {2020: 8.65, 2021: 8.75, 2022: 9.20, 2023: 9.95, 2024: 10.30, 2025: 10.55, 2026: 10.85},
    "31": {2020: 9.00, 2021: 9.00, 2022: 9.00, 2023: 10.50, 2024: 12.00, 2025: 13.50, 2026: 15.00},
    "32": {2020: 8.50, 2021: 9.25, 2022: 10.00, 2023: 10.75, 2024: 12.00, 2025: 12.00, 2026: 12.00},
    "33": {2020: 7.25, 2021: 7.25, 2022: 7.25, 2023: 7.25, 2024: 7.25, 2025: 7.25, 2026: 7.25},
    "34": {2020: 11.00, 2021: 12.00, 2022: 13.00, 2023: 14.13, 2024: 15.13, 2025: 15.49, 2026: 15.92},
    "35": {2020: 9.00, 2021: 10.50, 2022: 11.50, 2023: 12.00, 2024: 12.00, 2025: 12.00, 2026: 12.00},
    "36": {2020: 11.80, 2021: 12.50, 2022: 13.20, 2023: 14.20, 2024: 15.00, 2025: 15.50, 2026: 16.00},
    "37": {2020: 7.25, 2021: 7.25, 2022: 7.25, 2023: 7.25, 2024: 7.25, 2025: 7.25, 2026: 7.25},
    "38": {2020: 7.25, 2021: 7.25, 2022: 7.25, 2023: 7.25, 2024: 7.25, 2025: 7.25, 2026: 7.25},
    "39": {2020: 8.70, 2021: 8.80, 2022: 9.30, 2023: 10.10, 2024: 10.45, 2025: 10.70, 2026: 11.00},
    "40": {2020: 7.25, 2021: 7.25, 2022: 7.25, 2023: 7.25, 2024: 7.25, 2025: 7.25, 2026: 7.25},
    "41": {2020: 12.00, 2021: 12.75, 2022: 13.50, 2023: 14.20, 2024: 14.70, 2025: 14.70, 2026: 15.05},
    "42": {2020: 7.25, 2021: 7.25, 2022: 7.25, 2023: 7.25, 2024: 7.25, 2025: 7.25, 2026: 7.25},
    "44": {2020: 11.50, 2021: 11.50, 2022: 12.25, 2023: 13.00, 2024: 14.00, 2025: 15.00, 2026: 16.00},
    "45": {2020: 0, 2021: 0, 2022: 0, 2023: 0, 2024: 0, 2025: 0, 2026: 0},
    "46": {2020: 9.30, 2021: 9.45, 2022: 9.95, 2023: 10.80, 2024: 11.20, 2025: 11.50, 2026: 11.85},
    "47": {2020: 0, 2021: 0, 2022: 0, 2023: 0, 2024: 0, 2025: 0, 2026: 0},
    "48": {2020: 7.25, 2021: 7.25, 2022: 7.25, 2023: 7.25, 2024: 7.25, 2025: 7.25, 2026: 7.25},
    "49": {2020: 7.25, 2021: 7.25, 2022: 7.25, 2023: 7.25, 2024: 7.25, 2025: 7.25, 2026: 7.25},
    "50": {2020: 10.96, 2021: 11.75, 2022: 12.55, 2023: 13.18, 2024: 13.67, 2025: 14.01, 2026: 14.42},
    "51": {2020: 7.25, 2021: 9.50, 2022: 11.00, 2023: 12.00, 2024: 12.00, 2025: 12.41, 2026: 12.77},
    "53": {2020: 13.50, 2021: 13.69, 2022: 14.49, 2023: 15.74, 2024: 16.28, 2025: 16.66, 2026: 17.13},
    "54": {2020: 8.75, 2021: 8.75, 2022: 8.75, 2023: 8.75, 2024: 8.75, 2025: 8.75, 2026: 8.75},
    "55": {2020: 7.25, 2021: 7.25, 2022: 7.25, 2023: 7.25, 2024: 7.25, 2025: 7.25, 2026: 7.25},
    "56": {2020: 5.15, 2021: 5.15, 2022: 5.15, 2023: 5.15, 2024: 5.15, 2025: 5.15, 2026: 5.15},
}

# Quarter-start statutory basic rate after VZ ends. Retrieved 2026-08-16.
MIDYEAR: dict[tuple[str, int, int], float] = {
    ("12", 2023, 1): 11.00,
    ("12", 2023, 2): 11.00,
    ("12", 2023, 3): 11.00,
    ("12", 2023, 4): 12.00,
    ("12", 2024, 1): 12.00,
    ("12", 2024, 2): 12.00,
    ("12", 2024, 3): 12.00,
    ("12", 2024, 4): 13.00,
    ("12", 2025, 1): 13.00,
    ("12", 2025, 2): 13.00,
    ("12", 2025, 3): 13.00,
    ("12", 2025, 4): 14.00,
    ("12", 2026, 1): 14.00,
    ("12", 2026, 2): 14.00,
    ("12", 2026, 3): 14.00,
    ("11", 2023, 1): 16.10,
    ("11", 2023, 2): 16.10,
    ("11", 2023, 3): 17.00,
    ("11", 2024, 1): 17.00,
    ("11", 2024, 2): 17.00,
    ("11", 2024, 3): 17.50,
    ("11", 2025, 1): 17.50,
    ("11", 2025, 2): 17.50,
    ("11", 2025, 3): 17.95,
    ("41", 2023, 1): 13.50,
    ("41", 2023, 2): 13.50,
    ("41", 2023, 3): 14.20,
    ("41", 2024, 1): 14.20,
    ("41", 2024, 2): 14.20,
    ("41", 2024, 3): 14.70,
    ("41", 2025, 1): 14.70,
    ("41", 2025, 2): 14.70,
    ("41", 2025, 3): 15.05,
    ("32", 2023, 3): 11.25,
    ("32", 2023, 4): 11.25,
    ("32", 2024, 1): 11.25,
    ("32", 2024, 2): 11.25,
    ("32", 2024, 3): 12.00,
    ("09", 2023, 1): 14.00,
    ("09", 2023, 2): 15.00,
    ("02", 2025, 3): 13.00,
    ("02", 2026, 3): 14.00,
}

CPI_U_ANNUAL: dict[int, float] = {
    2000: 172.2,
    2001: 177.1,
    2002: 179.9,
    2003: 184.0,
    2004: 188.9,
    2005: 195.3,
    2006: 201.6,
    2007: 207.342,
    2008: 215.303,
    2009: 214.537,
    2010: 218.056,
    2011: 224.939,
    2012: 229.594,
    2013: 232.957,
    2014: 236.736,
    2015: 237.017,
    2016: 240.007,
    2017: 245.120,
    2018: 251.107,
    2019: 255.657,
    2020: 258.811,
    2021: 270.970,
    2022: 292.655,
    2023: 304.702,
    2024: 313.689,
    2025: 322.0,
    2026: 328.0,
}

LOCAL_MW_COUNTY_FIPS = {
    "06001",
    "06013",
    "06037",
    "06075",
    "06081",
    "06085",
    "06087",
    "08013",
    "08031",
    "17031",
    "24031",
    "24027",
    "27053",
    "35001",
    "36047",
    "36061",
    "36081",
    "36005",
    "36085",
    "36059",
    "36103",
    "36119",
    "41051",
    "53033",
    "53061",
    "53053",
}

TIP_CREDIT_STATES = {
    "01",
    "04",
    "05",
    "08",
    "09",
    "10",
    "12",
    "13",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "23",
    "24",
    "25",
    "26",
    "28",
    "29",
    "31",
    "33",
    "34",
    "35",
    "36",
    "37",
    "38",
    "39",
    "40",
    "42",
    "44",
    "45",
    "46",
    "47",
    "48",
    "49",
    "50",
    "51",
    "54",
    "55",
    "56",
}


def _applicable(state_basic: float) -> float:
    return max(FEDERAL_MW, state_basic)


def dol_extension(start_year: int = 2023, end_year: int = 2026) -> pl.DataFrame:
    rows = []
    for fips, by_year in DOL_JAN1.items():
        for year in range(start_year, end_year + 1):
            jan1 = by_year[year]
            for qtr in (1, 2, 3, 4):
                rate = MIDYEAR.get((fips, year, qtr), jan1)
                if (fips, year, qtr) not in MIDYEAR and qtr > 1:
                    for prev in range(qtr - 1, 0, -1):
                        if (fips, year, prev) in MIDYEAR:
                            rate = MIDYEAR[(fips, year, prev)]
                            break
                rows.append(
                    {
                        "state_fips": fips,
                        "year": year,
                        "qtr": qtr,
                        "mw_dol": _applicable(rate),
                        "state_basic": rate,
                    }
                )
    return pl.DataFrame(rows)


def download_vz_quarterly(dest_dir: Path | None = None) -> Path:
    """Download VZ v1.4.0 state Excel zip and extract the quarterly workbook."""
    dest_dir = dest_dir or (raw_dir() / "vz_state")
    dest_dir.mkdir(parents=True, exist_ok=True)
    xlsx = dest_dir / "mw_state_quarterly.xlsx"
    if xlsx.exists():
        return xlsx
    if not VZ_ZIP_URL.startswith("https://"):
        raise ValueError("refusing non-https VZ URL")
    with urlopen(VZ_ZIP_URL, timeout=120) as resp:  # noqa: S310
        blob = resp.read()
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        names = [n for n in zf.namelist() if "quarter" in n.lower() and n.endswith(".xlsx")]
        if not names:
            names = [n for n in zf.namelist() if n.endswith(".xlsx")]
        if not names:
            raise FileNotFoundError(f"no xlsx in VZ zip; members={zf.namelist()[:12]}")
        chosen = next((n for n in names if "quarterly" in n.lower()), names[0])
        xlsx.write_bytes(zf.read(chosen))
    return xlsx


def load_vz_quarterly(path: Path | None = None) -> pl.DataFrame:
    path = path or (raw_dir() / "vz_state" / "mw_state_quarterly.xlsx")
    df = pl.read_excel(path, engine="openpyxl")
    rename = {}
    for c in df.columns:
        cl = c.lower()
        if "fips" in cl:
            rename[c] = "state_fips"
        elif "quarterly date" in cl or cl == "quarter":
            rename[c] = "qdate"
        elif "federal" in cl:
            rename[c] = "fed_min"
        elif "state minimum" in cl or cl.endswith("state min"):
            rename[c] = "st_min"
    df = df.rename(rename)
    df = df.with_columns(
        pl.col("state_fips").cast(pl.Utf8).str.zfill(2),
        pl.col("qdate")
        .cast(pl.Utf8)
        .str.to_lowercase()
        .str.extract(r"^(\d{4})", 1)
        .cast(pl.Int64)
        .alias("year"),
        pl.col("qdate")
        .cast(pl.Utf8)
        .str.to_lowercase()
        .str.extract(r"q(\d)", 1)
        .cast(pl.Int64)
        .alias("qtr"),
        pl.max_horizontal(pl.col("fed_min"), pl.col("st_min")).alias("mw_vz"),
    )
    return (
        df.select(["state_fips", "year", "qtr", "mw_vz"])
        .with_columns(
            pl.col("year").cast(pl.Int64),
            pl.col("qtr").cast(pl.Int64),
            pl.col("mw_vz").cast(pl.Float64),
        )
        .filter(pl.col("state_fips").is_in(list(STATE_FIPS_NAMES)))
        .unique(subset=["state_fips", "year", "qtr"])
    )


def load_fixture_mw() -> pl.DataFrame:
    path = fixtures_dir() / "mw_sample.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    return pl.DataFrame(rows)


def _decorate(panel: pl.DataFrame) -> pl.DataFrame:
    cpi_df = pl.DataFrame({"year": list(CPI_U_ANNUAL), "cpi_u": list(CPI_U_ANNUAL.values())})
    base = CPI_U_ANNUAL[CPI_BASE_YEAR]
    panel = panel.join(cpi_df, on="year", how="left")
    panel = panel.with_columns(
        (pl.col("mw_nominal") * (base / pl.col("cpi_u"))).alias("mw_real_2024usd"),
        pl.col("state_fips").replace_strict(STATE_FIPS_NAMES, default=None).alias("state_name"),
        pl.col("state_fips").is_in(list(TIP_CREDIT_STATES)).alias("has_tip_credit"),
        pl.lit(str(RETRIEVED)).alias("retrieved_at"),
        pl.lit(FEDERAL_MW).alias("federal_floor"),
    )
    panel = panel.sort(["state_fips", "year", "qtr"])
    return panel.with_columns(
        (pl.col("mw_nominal") - pl.col("mw_nominal").shift(1).over("state_fips")).alias(
            "d_mw_nominal"
        ),
        (pl.col("mw_real_2024usd") - pl.col("mw_real_2024usd").shift(1).over("state_fips")).alias(
            "d_mw_real"
        ),
        (
            pl.col("mw_real_2024usd") / pl.col("mw_real_2024usd").shift(4).over("state_fips") - 1
        ).alias("real_pct_chg_4q"),
    )


def build_panel(*, offline: bool = False, download_vz: bool = True) -> pl.DataFrame:
    """VZ through 2022 + DOL 2023+. Offline mode uses the committed MW fixture + DOL."""
    dol = dol_extension().with_columns(
        pl.col("mw_dol").alias("mw_nominal"),
        pl.lit("dol_whd_extension").alias("source"),
        pl.lit(DOL_HIST_URL).alias("source_url"),
    )
    vz: pl.DataFrame | None = None
    if offline:
        fx = load_fixture_mw().with_columns(
            pl.col("mw_nominal").cast(pl.Float64),
            pl.lit("fixture").alias("source"),
            pl.lit("fixtures/mw_sample.json").alias("source_url"),
        )
        vz = fx
    elif download_vz:
        try:
            path = download_vz_quarterly()
            vz = load_vz_quarterly(path).with_columns(
                pl.col("mw_vz").alias("mw_nominal"),
                pl.lit("vaghul_zipperer_v1.4.0").alias("source"),
                pl.lit(VZ_RELEASE_URL).alias("source_url"),
            )
        except Exception as exc:
            print(f"VZ download/parse failed ({exc}); using DOL 2020+ only", flush=True)
            vz = None

    parts = []
    if vz is not None and vz.height:
        parts.append(
            vz.filter(pl.col("year") <= 2022).select(
                ["state_fips", "year", "qtr", "mw_nominal", "source", "source_url"]
            )
        )
    else:
        # DOL_JAN1 starts 2020 — use it as a fallback pre-2023 series.
        early = dol_extension(2020, 2022).with_columns(
            pl.col("mw_dol").alias("mw_nominal"),
            pl.lit("dol_whd_fallback_pre2023").alias("source"),
            pl.lit(DOL_HIST_URL).alias("source_url"),
        )
        parts.append(
            early.select(["state_fips", "year", "qtr", "mw_nominal", "source", "source_url"])
        )
    parts.append(dol.select(["state_fips", "year", "qtr", "mw_nominal", "source", "source_url"]))
    panel = pl.concat(parts, how="vertical")
    panel = panel.unique(subset=["state_fips", "year", "qtr"], keep="last")
    return _decorate(panel)


def write_panel(panel: pl.DataFrame) -> Path:
    dest = extracts_dir() / "mw_state_quarterly.parquet"
    dest.parent.mkdir(parents=True, exist_ok=True)
    panel.write_parquet(dest)
    summary = {
        "rows": panel.height,
        "years": [int(panel["year"].min()), int(panel["year"].max())],
        "states": panel["state_fips"].n_unique(),
        "sources": {
            "vz": VZ_RELEASE_URL,
            "dol_history": DOL_HIST_URL,
            "dol_state": DOL_STATE_URL,
            "dol_consolidated": DOL_CONS_URL,
            "berkeley_local": BERKELEY_LOCAL_URL,
        },
        "retrieved_at": str(RETRIEVED),
        "local_mw_county_n": len(LOCAL_MW_COUNTY_FIPS),
    }
    (extracts_dir() / "mw_panel_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return dest
