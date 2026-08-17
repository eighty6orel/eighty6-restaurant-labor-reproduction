"""Compare a live (or offline) results JSON to expected/headlines.json.

Offline results are not expected to match paper-grade values. Use --live
after a Pro pull. Rows tagged requires=live_pro_county are skipped offline.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from eighty6_repro.paths import expected_path, tables_dir


def _dig(obj: object, path: str) -> object:
    cur: object = obj
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list) and part.isdigit():
            cur = cur[int(part)]
        else:
            return None
    return cur


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare reproduction_results.json to expected headlines")
    parser.add_argument("--offline", action="store_true", help="Skip headlines that require a live Pro panel")
    parser.add_argument(
        "--results",
        type=Path,
        default=tables_dir() / "reproduction_results.json",
    )
    args = parser.parse_args()
    expected = json.loads(expected_path().read_text(encoding="utf-8"))
    results = json.loads(args.results.read_text(encoding="utf-8"))
    failures = 0
    checked = 0
    for item in expected["headlines"]:
        req = item.get("requires")
        if args.offline and req in {"live_pro_county", "census_adjacency"}:
            continue
        got = _dig(results, item["result_key"])
        exp = item["value"]
        tol = item.get("tolerance") or 0
        checked += 1
        if got is None:
            print(f"MISSING {item['id']} key={item['result_key']}")
            failures += 1
            continue
        if isinstance(exp, bool):
            ok = bool(got) is exp
        elif isinstance(exp, int | float) and not isinstance(exp, bool):
            ok = abs(float(got) - float(exp)) <= float(tol)
        else:
            ok = got == exp
        mark = "ok" if ok else "DIFF"
        if not ok:
            failures += 1
        print(f"{mark:4} {item['id']:40} expected={exp} got={got} tol={tol}")
    print(f"checked={checked} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
