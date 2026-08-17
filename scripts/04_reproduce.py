"""Reproduce RQ1–RQ10 tables and figures.

Offline (no key)::

    python scripts/04_reproduce.py --offline

Live (after 01–03)::

    python scripts/04_reproduce.py --live
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from eighty6_repro.cli import main

if __name__ == "__main__":
    main()
