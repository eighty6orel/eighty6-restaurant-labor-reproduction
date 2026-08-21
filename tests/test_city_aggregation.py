"""citygen-20260818: shares are sums, never the mean of county shares."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import polars as pl

_SRC = Path(__file__).resolve().parents[1] / "generations" / "20260818-citygen" / "src" / "aggregate_to_cities.py"
_SPEC = importlib.util.spec_from_file_location("citygen_aggregate", _SRC)
assert _SPEC is not None and _SPEC.loader is not None
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)


def test_city_wage_share_is_sum_not_mean() -> None:
    county = pl.DataFrame(
        {
            "area_fips": ["01001", "01003"],
            "year": [2024, 2024],
            "qtr": [1, 1],
            "wage_7225": [10.0, 90.0],
            "wage_all": [100.0, 400.0],
            "emp_7225": [1.0, 9.0],
            "emp_all": [10.0, 90.0],
            "est_7225": [1.0, 3.0],
        }
    )
    xw = pl.DataFrame(
        {
            "county_fips": ["01001", "01003"],
            "cbsa_code": ["99999", "99999"],
            "city_name": ["Test Metro", "Test Metro"],
        }
    )
    city = _MOD.aggregate_city_panel(county, xw)
    row = city.to_dicts()[0]
    assert row["generation"] == "citygen-20260818"
    assert row["wage_share_7225"] == (10.0 + 90.0) / (100.0 + 400.0)
    mean_of_shares = ((10.0 / 100.0) + (90.0 / 400.0)) / 2.0
    assert row["wage_share_7225"] != mean_of_shares
    assert row["n_counties_disclosed_7225"] == 2
    assert row["n_counties_delineated"] == 2
    assert row["coverage_7225"] == 1.0


def test_crosswalk_has_one_hundred_cities() -> None:
    xw = _MOD.load_crosswalk()
    assert xw["cbsa_code"].n_unique() == 100
    assert xw["county_fips"].n_unique() == 599
    assert "votes_dem" not in xw.columns
