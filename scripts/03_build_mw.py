"""Rebuild VZ + DOL minimum-wage exposure (not served by /v1/qcew/employment)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from eighty6_repro.mw import build_panel, write_panel


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild the statutory MW panel from public sources")
    parser.add_argument("--offline", action="store_true", help="Skip VZ download; use fixture + DOL")
    args = parser.parse_args()
    panel = build_panel(offline=args.offline, download_vz=not args.offline)
    dest = write_panel(panel)
    print(f"wrote {dest} ({panel.height} rows, years {panel['year'].min()}-{panel['year'].max()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
