"""citygen-20260818: aggregate disclosed county QCEW cells to top-100 CBSAs.

Do not use this module for county-generation (20260816) numbers.
Shares are recomputed from sums. Never average county shares.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

GENERATION_ID = "citygen-20260818"
HERE = Path(__file__).resolve().parents[1]
CROSSWALK = HERE / "data" / "county_to_cbsa_top100.json"


def load_crosswalk(path: Path | None = None) -> pl.DataFrame:
    p = path or CROSSWALK
    recs = json.loads(p.read_text(encoding="utf-8"))
    return pl.DataFrame(recs)


def aggregate_city_panel(county: pl.DataFrame, xw: pl.DataFrame) -> pl.DataFrame:
    """county must already have emp_7225, wage_7225, est_7225, emp_all, wage_all, area_fips."""
    n_delin = xw.group_by("cbsa_code").agg(pl.len().alias("n_counties_delineated"))
    mapped = county.join(
        xw.select([pl.col("county_fips").alias("area_fips"), "cbsa_code", "city_name"]),
        on="area_fips",
        how="inner",
    )
    cov = mapped.group_by(["cbsa_code", "year", "qtr"]).agg(
        pl.col("wage_7225").is_not_null().sum().alias("n_counties_disclosed_7225")
    ).join(n_delin, on="cbsa_code")
    sums = mapped.group_by(["cbsa_code", "city_name", "year", "qtr"]).agg(
        pl.col("wage_7225").sum().alias("wage_7225"),
        pl.col("wage_all").sum().alias("wage_all"),
        pl.col("emp_7225").sum().alias("emp_7225"),
        pl.col("est_7225").sum().alias("est_7225"),
    )
    panel = sums.join(cov, on=["cbsa_code", "year", "qtr"]).with_columns(
        (pl.col("wage_7225") / pl.col("wage_all").replace(0, None)).alias("wage_share_7225"),
        (pl.col("wage_7225") / pl.col("est_7225").replace(0, None)).alias("gwppr_7225"),
        (pl.col("n_counties_disclosed_7225") / pl.col("n_counties_delineated")).alias("coverage_7225"),
        pl.lit(GENERATION_ID).alias("generation"),
    )
    return panel


def main() -> None:
    from eighty6_repro.paths import extracts_dir, tables_dir

    xw = load_crosswalk()
    county_path = extracts_dir() / "county_panel.parquet"
    if not county_path.exists():
        raise SystemExit(f"missing {county_path}; run scripts/02_build_panel.py")
    county = pl.read_parquet(county_path)
    city = aggregate_city_panel(county, xw)
    out = tables_dir() / "citygen_20260818_panel.parquet"
    city.write_parquet(out)
    print(f"{GENERATION_ID}: wrote {out} rows={city.height} cities={city.select('cbsa_code').n_unique()}")


if __name__ == "__main__":
    main()
