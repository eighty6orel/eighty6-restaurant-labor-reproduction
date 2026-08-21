# County → city aggregation (G4) — generation `citygen-20260818`

**Audit-critical.** A reviewer who rebuilds city cells from a live Pro county pull must get the same shares as summing disclosed county numerators and denominators. **Never average county shares.**

## Definition

100 largest U.S. **Metropolitan Statistical Areas** (OMB CBSAs), ranked by Census Vintage 2024 `POPESTIMATE2024` (July 1, 2024). Membership = `LSAD == "County or equivalent"` rows in the same Census file (OMB Bulletin 23-01 delineations). Puerto Rico dropped. Micropolitan areas excluded.

Audience label = CBSA title left of the comma. Join key = 5-digit `cbsa_code`.

Rejected: principal-city counties only; Census places; QCEW MSA `agglvl` 81 (all-industry only in the eighty6 extract).

## Algebra

For city \(c\), quarter \(t\):

\[
W_{c,7225} = \sum_{i \in c,\, i\text{ disclosed}} W_{i,7225},\quad
W_{c,10} = \sum_{i \in c,\, i\text{ disclosed}} W_{i,10},\quad
\text{wage share}_c = W_{c,7225}/W_{c,10}
\]

Forbidden: mean of county wage shares.

Gross wages paid per restaurant: \(W_{c,7225}/N_{c,7225}\).

Employment-weighted MW: \(\sum_i MW_{s(i)} E_{i,7225} / \sum_i E_{i,7225}\).

Coverage: disclosed 7225 counties / counties in the delineation. Do not scale up suppressed cells.

## Code

`src/aggregate_to_cities.py` — generation comment `citygen-20260818` in the module docstring.

Committed crosswalk: `data/county_to_cbsa_top100.json` (retrieved 2026-08-18).
