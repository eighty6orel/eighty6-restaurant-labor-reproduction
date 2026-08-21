# Generation `citygen-20260818`

**Unit:** 100 largest U.S. Metropolitan Statistical Areas (OMB CBSAs).  
**Not:** the county-generation numbers in `papers/rq/`.  
**Audit-critical:** [`methods/city_aggregation.md`](methods/city_aggregation.md).

This folder is how a stranger turns a live county pull into city-metro cells. It does not contain QCEW extracts (those come from the eighty6 API on a Pro key).

```text
# After a live county pull and panel build
python generations/20260818-citygen/src/aggregate_to_cities.py
```

Committed crosswalk: `data/county_to_cbsa_top100.json` (Census Vintage 2024 CBSA components, retrieved 2026-08-18). Source URLs are in `data/crosswalk_meta.json`.

City-level RQ estimators from the later city generation are **not** in this client. The public product here is the geography rebuild so county and city numbers cannot be conflated.
