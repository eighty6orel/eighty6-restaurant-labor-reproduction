"""Locked study filters, plan limits, and public source URLs.

These constants match the Wage Share Restaurant Health papers (RQ1–RQ10).
They are the only geography / NAICS / ownership choices the reproduction uses.
"""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[1]

DEFAULT_API_BASE = "https://www.eighty6data.com/api"
USER_AGENT = "eighty6-restaurant-labor-reproduction/0.1"

# --- QCEW filters (locked before estimation) ---
OWNERSHIP_PRIVATE = "5"
SIZE_ALL = "0"
DISCLOSURE_SUPPRESSED = "N"

IND_ALL = "10"
IND_FOOD_DRINK_3 = "722"
IND_RESTAURANTS_4 = "7225"
IND_FSR = "722511"
IND_LSR = "722513"
IND_CAFETERIA = "722514"
IND_SNACK = "722515"
IND_FSR_2007 = "722110"
IND_LSR_2007 = "722211"
IND_CAFETERIA_2007 = "722212"
IND_SNACK_2007 = "722213"
IND_FSR_4_2007 = "7221"
IND_LSR_4_2007 = "7222"

FSR_CODES = (IND_FSR, IND_FSR_2007)
LSR_OTHER_CODES = (
    IND_LSR,
    IND_CAFETERIA,
    IND_SNACK,
    IND_LSR_2007,
    IND_CAFETERIA_2007,
    IND_SNACK_2007,
)
RESTAURANT_4_CODES = (IND_RESTAURANTS_4, IND_FSR_4_2007, IND_LSR_4_2007)
RESTAURANT_EXTRACT_CODES = (
    IND_ALL,
    IND_FOOD_DRINK_3,
    *RESTAURANT_4_CODES,
    *FSR_CODES,
    *LSR_OTHER_CODES,
)

# County private all-industry = agglvl 71; 4-digit = 76; 6-digit = 78.
# State: 51 / 56 / 58. National: 11 / 16 / 18.
AGGLVL_COUNTY_TOTAL = "71"
AGGLVL_COUNTY_4 = "76"
AGGLVL_COUNTY_6 = "78"
AGGLVL_STATE_TOTAL = "51"
AGGLVL_STATE_4 = "56"
AGGLVL_STATE_6 = "58"
AGGLVL_US_TOTAL = "11"
AGGLVL_US_4 = "16"
AGGLVL_US_6 = "18"

PRIMARY_WINDOW = (2014, 2025)
SENSITIVITY_WINDOW = (2001, 2025)
INFERENCE_EXCLUDE_YEARS = (2020, 2021)

EVENT_REAL_PCT_THRESHOLD = 0.10
CPI_BASE_YEAR = 2024
FEDERAL_MW = 7.25

PLAN_LIMITS = {
    "basic": {"rpm": 60, "max_rows": 1_000, "max_date_range_days": 365},
    "pro": {"rpm": 300, "max_rows": 10_000, "max_date_range_days": 3_650},
}

# Production OpenAPI (verified 2026-08-17): GET /v1/qcew/employment
# accepts a single industry_code / area_fips / agglvl_code per request.
API_SINGLE_FILTERS = ("industry_code", "area_fips", "agglvl_code")

VZ_RELEASE_URL = "https://github.com/benzipperer/historicalminwage/releases/tag/v1.4.0"
VZ_XLSX_CANDIDATES = (
    "https://github.com/benzipperer/historicalminwage/releases/download/v1.4.0/mw_state_quarterly.xlsx",
    "https://github.com/benzipperer/historicalminwage/raw/v1.4.0/mw_state_quarterly.xlsx",
)
DOL_HIST_URL = "https://www.dol.gov/agencies/whd/state/minimum-wage/history"
DOL_STATE_URL = "https://www.dol.gov/agencies/whd/minimum-wage/state"
DOL_CONS_URL = "https://www.dol.gov/agencies/whd/mw-consolidated"
BERKELEY_LOCAL_URL = (
    "https://laborcenter.berkeley.edu/inventory-of-us-city-and-county-minimum-wage-ordinances/"
)
CENSUS_ADJ_URL = "https://www2.census.gov/geo/docs/reference/county_adjacency.txt"
CPI_URL = "https://www.bls.gov/cpi/"

STATE_FIPS_NAMES: dict[str, str] = {
    "01": "Alabama",
    "02": "Alaska",
    "04": "Arizona",
    "05": "Arkansas",
    "06": "California",
    "08": "Colorado",
    "09": "Connecticut",
    "10": "Delaware",
    "11": "District of Columbia",
    "12": "Florida",
    "13": "Georgia",
    "15": "Hawaii",
    "16": "Idaho",
    "17": "Illinois",
    "18": "Indiana",
    "19": "Iowa",
    "20": "Kansas",
    "21": "Kentucky",
    "22": "Louisiana",
    "23": "Maine",
    "24": "Maryland",
    "25": "Massachusetts",
    "26": "Michigan",
    "27": "Minnesota",
    "28": "Mississippi",
    "29": "Missouri",
    "30": "Montana",
    "31": "Nebraska",
    "32": "Nevada",
    "33": "New Hampshire",
    "34": "New Jersey",
    "35": "New Mexico",
    "36": "New York",
    "37": "North Carolina",
    "38": "North Dakota",
    "39": "Ohio",
    "40": "Oklahoma",
    "41": "Oregon",
    "42": "Pennsylvania",
    "44": "Rhode Island",
    "45": "South Carolina",
    "46": "South Dakota",
    "47": "Tennessee",
    "48": "Texas",
    "49": "Utah",
    "50": "Vermont",
    "51": "Virginia",
    "53": "Washington",
    "54": "West Virginia",
    "55": "Wisconsin",
    "56": "Wyoming",
}
