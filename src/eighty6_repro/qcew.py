"""Study-shaped QCEW pulls: locked filters, year chunks, industry × agglvl loops."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import polars as pl

from eighty6_repro.client import Eighty6Client
from eighty6_repro.config import (
    AGGLVL_COUNTY_4,
    AGGLVL_COUNTY_6,
    AGGLVL_COUNTY_TOTAL,
    AGGLVL_STATE_4,
    AGGLVL_STATE_6,
    AGGLVL_STATE_TOTAL,
    AGGLVL_US_4,
    AGGLVL_US_6,
    AGGLVL_US_TOTAL,
    OWNERSHIP_PRIVATE,
    PRIMARY_WINDOW,
    RESTAURANT_EXTRACT_CODES,
    SIZE_ALL,
)
from eighty6_repro.paths import extracts_dir, raw_dir

# One request per (industry, agglvl) because the API takes a single code each.
STUDY_SLICES: tuple[tuple[str, str], ...] = (
    ("10", AGGLVL_US_TOTAL),
    ("7225", AGGLVL_US_4),
    ("7221", AGGLVL_US_4),
    ("7222", AGGLVL_US_4),
    ("722511", AGGLVL_US_6),
    ("722513", AGGLVL_US_6),
    ("722514", AGGLVL_US_6),
    ("722515", AGGLVL_US_6),
    ("722110", AGGLVL_US_6),
    ("722211", AGGLVL_US_6),
    ("722212", AGGLVL_US_6),
    ("722213", AGGLVL_US_6),
    ("10", AGGLVL_STATE_TOTAL),
    ("7225", AGGLVL_STATE_4),
    ("7221", AGGLVL_STATE_4),
    ("7222", AGGLVL_STATE_4),
    ("722511", AGGLVL_STATE_6),
    ("722513", AGGLVL_STATE_6),
    ("722514", AGGLVL_STATE_6),
    ("722515", AGGLVL_STATE_6),
    ("10", AGGLVL_COUNTY_TOTAL),
    ("7225", AGGLVL_COUNTY_4),
    ("7221", AGGLVL_COUNTY_4),
    ("7222", AGGLVL_COUNTY_4),
    ("722511", AGGLVL_COUNTY_6),
    ("722513", AGGLVL_COUNTY_6),
    ("722514", AGGLVL_COUNTY_6),
    ("722515", AGGLVL_COUNTY_6),
    ("722110", AGGLVL_COUNTY_6),
    ("722211", AGGLVL_COUNTY_6),
    ("722212", AGGLVL_COUNTY_6),
    ("722213", AGGLVL_COUNTY_6),
)

NATIONAL_SLICES = tuple(s for s in STUDY_SLICES if s[1] in {AGGLVL_US_TOTAL, AGGLVL_US_4, AGGLVL_US_6})


def rows_to_frame(rows: Iterable[dict[str, Any]]) -> pl.DataFrame:
    data = list(rows)
    if not data:
        return pl.DataFrame()
    return pl.DataFrame(data)


def pull_slice(
    client: Eighty6Client,
    *,
    industry_code: str,
    agglvl_code: str,
    start_year: int,
    end_year: int,
    area_fips: str | None = None,
    persist_raw: bool = False,
) -> pl.DataFrame:
    """Pull one industry × agglvl across plan-legal year chunks, paginating each."""
    frames: list[pl.DataFrame] = []
    for y0, y1 in client.year_chunks(start_year, end_year):
        kwargs: dict[str, Any] = {
            "industry_code": industry_code,
            "agglvl_code": agglvl_code,
            "ownership_code": OWNERSHIP_PRIVATE,
            "size_code": SIZE_ALL,
        }
        if area_fips:
            kwargs["area_fips"] = area_fips
        if y0 == y1:
            kwargs["year"] = y0
        else:
            kwargs["start_year"] = y0
            kwargs["end_year"] = y1
        page_i = 0
        for page in client.iter_pages(**kwargs):
            if persist_raw:
                dest = raw_dir() / (
                    f"qcew_{industry_code}_{agglvl_code}_{y0}_{y1}_{page.offset}.json"
                )
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(json.dumps(page.data), encoding="utf-8")
            if page.data:
                frames.append(pl.DataFrame(page.data))
            page_i += 1
    if not frames:
        return pl.DataFrame()
    return pl.concat(frames, how="vertical_relaxed")


def pull_study(
    client: Eighty6Client,
    *,
    start_year: int = PRIMARY_WINDOW[0],
    end_year: int = PRIMARY_WINDOW[1],
    geography: str = "all",
    persist_raw: bool = False,
) -> pl.DataFrame:
    """Pull the locked restaurant + all-industry slice.

    geography: ``national`` (US series only), ``all`` (US + state + county).
    Full county coverage needs a Pro plan; Basic can do national plus a sample.
    """
    if geography == "national":
        slices = NATIONAL_SLICES
    else:
        slices = STUDY_SLICES
    frames: list[pl.DataFrame] = []
    for industry, agglvl in slices:
        print(f"  pulling industry={industry} agglvl={agglvl} {start_year}-{end_year}", flush=True)
        df = pull_slice(
            client,
            industry_code=industry,
            agglvl_code=agglvl,
            start_year=start_year,
            end_year=end_year,
            persist_raw=persist_raw,
        )
        if df.height:
            frames.append(df)
            print(f"    {df.height:,} rows", flush=True)
    if not frames:
        return pl.DataFrame()
    out = pl.concat(frames, how="vertical_relaxed")
    dest = extracts_dir() / "qcew_slice.parquet"
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.write_parquet(dest)
    return out


def load_qcew(path: Path | None = None) -> pl.DataFrame:
    path = path or (extracts_dir() / "qcew_slice.parquet")
    return pl.read_parquet(path)


def assert_study_codes(df: pl.DataFrame) -> None:
    extra = set(df["industry_code"].unique()) - set(RESTAURANT_EXTRACT_CODES)
    if extra:
        raise ValueError(f"unexpected industry codes in extract: {sorted(extra)}")
