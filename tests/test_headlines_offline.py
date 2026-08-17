"""Offline reproduce runs and fixture-scale headline identities."""

from __future__ import annotations

import json
from pathlib import Path

from eighty6_repro.cli import reproduce
from eighty6_repro.paths import expected_path


def test_expected_headlines_cover_rq1_to_rq10() -> None:
    payload = json.loads(expected_path().read_text(encoding="utf-8"))
    rqs = {item["rq"] for item in payload["headlines"]}
    assert rqs == {f"RQ{i}" for i in range(1, 11)}
    for item in payload["headlines"]:
        assert item["inference_tier"]
        assert item["script"] in {"scripts/04_reproduce.py", "scripts/03_build_mw.py"}
        assert "tolerance" in item


def test_offline_reproduce_writes_results(tmp_path: Path, monkeypatch) -> None:
    results = reproduce(offline=True, download_adj=False)
    assert results["mode"] == "offline"
    assert results["raw_rows"] > 0
    assert results["rq1"]["inference_tier"] == "descriptive"
    assert results["rq2"]["inference_tier"] == "association"
    assert results["rq3"]["inference_tier"] == "measurement"
    assert results["rq7"]["inference_tier"] == "association"
    assert results["rq8"]["cs_causal"] is False
    # Fixture-scale: US shares exist and stay in (0, 1)
    ws = results["rq1"]["us_2024q1_ws"]
    assert ws is not None and 0 < ws < 1
    # RQ5 trough is negative for FSR on the illustrative national path
    if results["rq5"].get("fsr_trough_pct") is not None:
        assert results["rq5"]["fsr_trough_pct"] < 0
