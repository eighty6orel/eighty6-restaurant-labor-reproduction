"""Live pull of the study QCEW slice → data/extracts/qcew_slice.parquet (gitignored)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from eighty6_repro.client import Eighty6Client, load_settings
from eighty6_repro.config import PRIMARY_WINDOW, SENSITIVITY_WINDOW
from eighty6_repro.qcew import pull_study


def main() -> int:
    parser = argparse.ArgumentParser(description="Pull the locked QCEW slice from the eighty6 API")
    parser.add_argument("--start-year", type=int, default=PRIMARY_WINDOW[0])
    parser.add_argument("--end-year", type=int, default=PRIMARY_WINDOW[1])
    parser.add_argument(
        "--geography",
        choices=("national", "all"),
        default="all",
        help="national = US series only (Basic-friendly); all = US+state+county (Pro)",
    )
    parser.add_argument("--sensitivity", action="store_true", help="Use 2001–2025 window")
    parser.add_argument("--persist-raw", action="store_true")
    args = parser.parse_args()
    start, end = args.start_year, args.end_year
    if args.sensitivity:
        start, end = SENSITIVITY_WINDOW
    key, base, plan = load_settings()
    if not key:
        print("E86_API_KEY is empty. Create a key at https://www.eighty6data.com")
        print("Offline demo: python scripts/04_reproduce.py --offline")
        return 2
    if args.geography == "all" and plan == "basic":
        print("Warning: full county panel on Basic is slow (1,000 rows/page, 365-day chunks).")
        print("Pro is the honest path for paper-grade county results.")
    with Eighty6Client(api_key=key, api_base=base, plan=plan) as client:
        df = pull_study(
            client,
            start_year=start,
            end_year=end,
            geography=args.geography,
            persist_raw=args.persist_raw,
        )
    print(f"wrote {df.height:,} rows")
    return 0 if df.height else 1


if __name__ == "__main__":
    raise SystemExit(main())
