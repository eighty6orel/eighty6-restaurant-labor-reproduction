"""Console entry: ``e86-repro --offline`` or ``python -m eighty6_repro``."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from typing import Any

import polars as pl

from eighty6_repro.fixtures import load_qcew_fixture
from eighty6_repro.mw import build_panel, write_panel
from eighty6_repro.panel import cast_decimals, county_panel, merge_mw, state_panel, us_panel
from eighty6_repro.paths import ensure_output_dirs, extracts_dir, tables_dir
from eighty6_repro.rqs import primary_sample, rq01, rq02, rq03, rq04, rq05, rq06, rq07, rq08, rq09, rq10


def reproduce(*, offline: bool = True, download_adj: bool = True) -> dict[str, Any]:
    """Run RQ1–RQ10 on fixtures (offline) or a previously pulled extract (live)."""
    ensure_output_dirs()
    if offline:
        raw = load_qcew_fixture()
        mw = build_panel(offline=True, download_vz=False)
    else:
        raw = pl.read_parquet(extracts_dir() / "qcew_slice.parquet")
        mw_path = extracts_dir() / "mw_state_quarterly.parquet"
        mw = pl.read_parquet(mw_path) if mw_path.exists() else build_panel(offline=False)
    write_panel(mw)
    county = cast_decimals(merge_mw(county_panel(raw), mw))
    state = cast_decimals(merge_mw(state_panel(raw), mw))
    us = cast_decimals(us_panel(raw))
    d = primary_sample(county)
    results: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "mode": "offline" if offline else "live",
        "raw_rows": raw.height,
        "county_rows": county.height,
        "rq1": rq01(us, county),
        "rq2": rq02(county),
        "rq3": rq03(county),
        "rq5": rq05(us),
        "rq6": rq06(county, mw),
    }
    results["rq4"] = rq04(county, results["rq3"])
    results["rq7"] = rq07(d)
    results["rq8"] = rq08(state)
    results["rq9"] = rq09(county, download_adj=download_adj and not offline)
    results["rq10"] = rq10(d)
    dest = tables_dir() / "reproduction_results.json"
    dest.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    return results


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Reproduce RQ1–RQ10 from fixtures or a live extract")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use committed fixtures (no API key). Default if no extract exists.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use data/extracts/qcew_slice.parquet from scripts/01_pull_qcew.py",
    )
    parser.add_argument(
        "--no-adjacency",
        action="store_true",
        help="Skip Census adjacency download (RQ9 will record a gap)",
    )
    args = parser.parse_args(argv)
    offline = not args.live
    if args.offline:
        offline = True
    results = reproduce(offline=offline, download_adj=not args.no_adjacency)
    print(f"mode={results['mode']} raw_rows={results['raw_rows']} county_rows={results['county_rows']}")
    print(f"wrote {tables_dir() / 'reproduction_results.json'}")


if __name__ == "__main__":
    main()
