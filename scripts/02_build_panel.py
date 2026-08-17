"""Build county / state / US analysis panels from a QCEW extract + MW panel."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import polars as pl

from eighty6_repro.panel import cast_decimals, county_panel, merge_mw, state_panel, us_panel
from eighty6_repro.paths import extracts_dir


def main() -> int:
    raw_path = extracts_dir() / "qcew_slice.parquet"
    mw_path = extracts_dir() / "mw_state_quarterly.parquet"
    if not raw_path.exists():
        print("missing data/extracts/qcew_slice.parquet — run scripts/01_pull_qcew.py")
        return 2
    if not mw_path.exists():
        print("missing MW panel — run scripts/03_build_mw.py")
        return 2
    raw = pl.read_parquet(raw_path)
    mw = pl.read_parquet(mw_path)
    county = cast_decimals(merge_mw(county_panel(raw), mw))
    state = cast_decimals(merge_mw(state_panel(raw), mw))
    us = cast_decimals(us_panel(raw))
    extracts_dir().mkdir(parents=True, exist_ok=True)
    county.write_parquet(extracts_dir() / "county_panel.parquet")
    state.write_parquet(extracts_dir() / "state_panel.parquet")
    us.write_parquet(extracts_dir() / "us_panel.parquet")
    print(f"county={county.height:,} state={state.height:,} us={us.height:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
