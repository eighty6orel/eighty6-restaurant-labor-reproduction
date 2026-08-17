"""Share identities on the committed fixtures."""

from __future__ import annotations

import math

from eighty6_repro.fixtures import load_qcew_fixture
from eighty6_repro.metrics import usable_qcew_rows
from eighty6_repro.mw import build_panel
from eighty6_repro.panel import cast_decimals, county_panel, merge_mw, us_panel


def test_disclosure_drops_n_and_nulls() -> None:
    raw = load_qcew_fixture()
    n_suppressed = raw.filter(raw["disclosure_code"] == "N").height
    usable = usable_qcew_rows(raw)
    assert n_suppressed >= 1
    assert usable.filter(usable["disclosure_code"] == "N").height == 0
    assert usable["total_qtrly_wages"].null_count() == 0


def test_wage_share_is_ratio_of_same_cell() -> None:
    raw = load_qcew_fixture()
    us = us_panel(raw)
    row = us.filter((us["year"] == 2024) & (us["qtr"] == 1)).to_dicts()[0]
    expected = float(row["wage_7225"]) / float(row["wage_all"])
    assert math.isclose(float(row["wage_share_7225"]), expected, rel_tol=0, abs_tol=1e-12)
    assert 0 < float(row["wage_share_7225"]) < 1
    assert 0 < float(row["emp_share_7225"]) < 1
    assert float(row["epe_7225"]) == float(row["emp_7225"]) / float(row["est_7225"])


def test_county_shares_in_unit_interval() -> None:
    raw = load_qcew_fixture()
    county = county_panel(raw)
    ws = county.drop_nulls(["wage_share_7225"])["wage_share_7225"]
    assert ws.min() > 0
    assert ws.max() < 1
    assert county["area_fips"].n_unique() <= 10


def test_kaitz_is_mw_over_implied_hourly() -> None:
    raw = load_qcew_fixture()
    mw = build_panel(offline=True, download_vz=False)
    county = cast_decimals(merge_mw(county_panel(raw), mw))
    row = county.filter(
        (county["year"] == 2024) & (county["qtr"] == 1) & county["kaitz_7225"].is_not_null()
    ).to_dicts()[0]
    expected = float(row["mw_nominal"]) / (float(row["aww_7225"]) / 40.0)
    assert math.isclose(float(row["kaitz_7225"]), expected, rel_tol=0, abs_tol=1e-9)
