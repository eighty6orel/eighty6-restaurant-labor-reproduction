"""Health + auth smoke test. Prints plan-safe diagnostics; never dumps the key."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from eighty6_repro.client import Eighty6APIError, Eighty6Client, load_settings, mask_key
from eighty6_repro.config import DEFAULT_API_BASE, PLAN_LIMITS


def main() -> int:
    key, base, plan = load_settings()
    limits = PLAN_LIMITS[plan]
    print(f"api_base     {base}")
    print(f"documented   {DEFAULT_API_BASE}")
    print(f"plan         {plan}  (max_rows={limits['max_rows']}, date_days={limits['max_date_range_days']})")
    print(f"api_key      {mask_key(key)}")
    with Eighty6Client(api_key=key, api_base=base, plan=plan) as client:
        try:
            health = client.health()
            print(f"health       {health}")
        except Eighty6APIError as exc:
            print(f"health       FAIL {exc}")
            return 1
        if not key:
            print("auth         skipped (no E86_API_KEY; offline fixtures still work)")
            return 0
        try:
            page = client.fetch_page(
                year=2024,
                qtr=1,
                area_fips="US000",
                industry_code="7225",
                ownership_code="5",
                size_code="0",
                agglvl_code="16",
                limit=5,
            )
            print(f"auth         ok  rows={len(page.data)} total={page.total} has_more={page.has_more}")
        except Eighty6APIError as exc:
            print(f"auth         FAIL {exc}")
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
