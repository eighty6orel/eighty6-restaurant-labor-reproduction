"""One-off generator for committed public-safe fixtures. Not part of the user path."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures"

QUARTERS = [
    (2014, 1),
    (2019, 1),
    (2019, 4),
    (2020, 2),
    (2023, 1),
    (2023, 4),
    (2024, 1),
    (2024, 4),
]

COUNTIES = [
    ("06037", "Los Angeles County, California", "06"),
    ("06075", "San Francisco County, California", "06"),
    ("48201", "Harris County, Texas", "48"),
    ("48113", "Dallas County, Texas", "48"),
    ("36061", "New York County, New York", "36"),
    ("36047", "Kings County, New York", "36"),
    ("17031", "Cook County, Illinois", "17"),
    ("53033", "King County, Washington", "53"),
]


def row(
    year: int,
    qtr: int,
    area_fips: str,
    area_title: str,
    industry: str,
    agglvl: str,
    emp: float,
    wage: float,
    est: float,
    aww: float,
    disclosure: str | None = None,
) -> dict:
    return {
        "year": year,
        "qtr": qtr,
        "area_fips": area_fips,
        "area_title": area_title,
        "industry_code": industry,
        "industry_title": {
            "10": "Total, all industries",
            "7225": "Restaurants and other eating places",
            "722511": "Full-service restaurants",
            "722513": "Limited-service restaurants",
            "722514": "Cafeterias, grill buffets, and buffets",
        }.get(industry, industry),
        "agglvl_code": agglvl,
        "ownership_code": "5",
        "size_code": "0",
        "disclosure_code": disclosure,
        "annual_avg_emplvl": emp,
        "total_qtrly_wages": wage,
        "qtrly_estabs": est,
        "avg_wkly_wage": aww,
    }


def us_series() -> list[dict]:
    # Illustrative national path with a 2020Q2 FSR trough.
    path = {
        (2014, 1): (110_000_000, 2_700_000, 5_200_000, 4_800_000),
        (2019, 1): (120_000_000, 9_900_000, 5_400_000, 5_300_000),
        (2019, 4): (121_000_000, 10_000_000, 5_432_197, 5_358_195),
        (2020, 2): (105_000_000, 7_200_000, 2_791_554, 4_434_843),
        (2023, 1): (125_000_000, 10_400_000, 5_200_000, 5_400_000),
        (2023, 4): (126_000_000, 10_500_000, 5_250_000, 5_500_000),
        (2024, 1): (128_000_000, 10_550_000, 5_280_000, 5_550_000),
        (2024, 4): (129_000_000, 10_700_000, 5_298_996, 5_609_603),
    }
    # wage_all chosen so 2014Q1 ws ~ 2.45% and 2024Q1 ws ~ 2.70% if we set restaurant wages.
    wage_all = {
        (2014, 1): 1_800_000_000_000,
        (2019, 1): 2_200_000_000_000,
        (2019, 4): 2_250_000_000_000,
        (2020, 2): 2_000_000_000_000,
        (2023, 1): 2_600_000_000_000,
        (2023, 4): 2_650_000_000_000,
        (2024, 1): 2_700_000_000_000,
        (2024, 4): 2_750_000_000_000,
    }
    wage_7225 = {
        (2014, 1): 0.024534 * wage_all[(2014, 1)],
        (2019, 1): 0.0260 * wage_all[(2019, 1)],
        (2019, 4): 0.0262 * wage_all[(2019, 4)],
        (2020, 2): 0.0220 * wage_all[(2020, 2)],
        (2023, 1): 0.0268 * wage_all[(2023, 1)],
        (2023, 4): 0.0269 * wage_all[(2023, 4)],
        (2024, 1): 0.027005 * wage_all[(2024, 1)],
        (2024, 4): 0.0271 * wage_all[(2024, 4)],
    }
    rows = []
    for (y, q), (emp_all, emp_r, emp_fsr, emp_lsr) in path.items():
        wa, wr = wage_all[(y, q)], wage_7225[(y, q)]
        rows.append(row(y, q, "US000", "U.S. TOTAL", "10", "11", emp_all, wa, 8_000_000, 900))
        rows.append(row(y, q, "US000", "U.S. TOTAL", "7225", "16", emp_r, wr, 650_000, 420))
        rows.append(
            row(y, q, "US000", "U.S. TOTAL", "722511", "18", emp_fsr, wr * 0.55, 320_000, 450)
        )
        rows.append(
            row(y, q, "US000", "U.S. TOTAL", "722513", "18", emp_lsr, wr * 0.45, 330_000, 390)
        )
    return rows


def county_series() -> list[dict]:
    rows = []
    # One suppressed cell to document disclosure handling.
    rows.append(
        row(2024, 1, "06037", "Los Angeles County, California", "722514", "78", None, None, 10, None, "N")  # type: ignore[arg-type]
    )
    rows[-1]["annual_avg_emplvl"] = None
    rows[-1]["total_qtrly_wages"] = None
    rows[-1]["avg_wkly_wage"] = None
    for i, (fips, title, _st) in enumerate(COUNTIES):
        base_emp_all = 400_000 + i * 50_000
        share = 0.02 + i * 0.004
        for y, q in QUARTERS:
            shock = 0.72 if (y, q) == (2020, 2) else 1.0
            emp_all = base_emp_all * (1 + 0.01 * (y - 2014))
            emp_r = emp_all * share * shock
            emp_fsr = emp_r * 0.52
            emp_lsr = emp_r * 0.48
            wage_all = emp_all * 12_000
            wage_r = wage_all * share * 0.85
            est_r = max(80, emp_r / (18 + i))
            aww_r = 380 + i * 15 + (y - 2014) * 8
            rows.append(row(y, q, fips, title, "10", "71", emp_all, wage_all, 20_000, 900))
            rows.append(row(y, q, fips, title, "7225", "76", emp_r, wage_r, est_r, aww_r))
            rows.append(
                row(y, q, fips, title, "722511", "78", emp_fsr, wage_r * 0.55, est_r * 0.5, aww_r + 20)
            )
            rows.append(
                row(y, q, fips, title, "722513", "78", emp_lsr, wage_r * 0.45, est_r * 0.5, aww_r - 15)
            )
    return rows


def mw_sample() -> list[dict]:
    rates = {
        "06": {2014: 8.00, 2019: 12.00, 2020: 13.00, 2023: 15.50, 2024: 16.00},
        "48": {2014: 7.25, 2019: 7.25, 2020: 7.25, 2023: 7.25, 2024: 7.25},
        "36": {2014: 8.00, 2019: 11.10, 2020: 11.80, 2023: 14.20, 2024: 15.00},
        "17": {2014: 8.25, 2019: 8.25, 2020: 10.00, 2023: 13.00, 2024: 14.00},
        "53": {2014: 9.32, 2019: 12.00, 2020: 13.50, 2023: 15.74, 2024: 16.28},
    }
    rows = []
    for st, by_year in rates.items():
        for y, q in QUARTERS:
            rows.append({"state_fips": st, "year": y, "qtr": q, "mw_nominal": by_year[y]})
    return rows


def main() -> None:
    FIX.mkdir(parents=True, exist_ok=True)
    (FIX / "qcew_national_sample.json").write_text(
        json.dumps(us_series(), indent=2), encoding="utf-8"
    )
    (FIX / "qcew_county_sample.json").write_text(
        json.dumps(county_series(), indent=2), encoding="utf-8"
    )
    (FIX / "mw_sample.json").write_text(json.dumps(mw_sample(), indent=2), encoding="utf-8")
    print("wrote fixtures")


if __name__ == "__main__":
    main()
