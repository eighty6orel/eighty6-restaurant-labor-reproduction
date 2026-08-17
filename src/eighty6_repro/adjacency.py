"""Census county adjacency → cross-state border pairs (RQ9).

Source (same file the study used):
https://www2.census.gov/geo/docs/reference/county_adjacency.txt
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.request import urlretrieve

import polars as pl

from eighty6_repro.config import CENSUS_ADJ_URL
from eighty6_repro.paths import raw_dir


def adjacency_path() -> Path:
    return raw_dir() / "county_adjacency.txt"


def download_adjacency(path: Path | None = None) -> Path:
    path = path or adjacency_path()
    if path.exists():
        return path
    if not CENSUS_ADJ_URL.startswith("https://"):
        raise ValueError(f"refusing non-https adjacency URL: {CENSUS_ADJ_URL}")
    path.parent.mkdir(parents=True, exist_ok=True)
    urlretrieve(CENSUS_ADJ_URL, path)  # noqa: S310
    return path


def parse_adjacency(path: Path | None = None) -> pl.DataFrame:
    path = path or adjacency_path()
    text = path.read_text(encoding="latin-1")
    pairs: list[tuple[str, str]] = []
    current: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        nums = re.findall(r"\b(\d{5})\b", line)
        if not nums:
            continue
        if not line.startswith(" ") and not line.startswith("\t"):
            current = nums[0]
            for n in nums[1:]:
                if n != current:
                    a, b = sorted((current, n))
                    pairs.append((a, b))
        else:
            if current is None:
                continue
            for n in nums:
                if n != current:
                    a, b = sorted((current, n))
                    pairs.append((a, b))
    df = pl.DataFrame({"fips_a": [p[0] for p in pairs], "fips_b": [p[1] for p in pairs]}).unique()
    df = df.with_columns(
        pl.col("fips_a").str.slice(0, 2).alias("st_a"),
        pl.col("fips_b").str.slice(0, 2).alias("st_b"),
    )
    return df.with_columns((pl.col("st_a") != pl.col("st_b")).alias("cross_state"))
