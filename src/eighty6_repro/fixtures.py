"""Load the committed QCEW-shaped samples for offline runs."""

from __future__ import annotations

import json

import polars as pl

from eighty6_repro.paths import fixtures_dir


def load_qcew_fixture() -> pl.DataFrame:
    rows: list[dict] = []
    for name in ("qcew_national_sample.json", "qcew_county_sample.json"):
        path = fixtures_dir() / name
        rows.extend(json.loads(path.read_text(encoding="utf-8")))
    return pl.DataFrame(rows)
