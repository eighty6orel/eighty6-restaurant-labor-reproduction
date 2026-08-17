# Papers and research questions

Reading order is Paper 1 → 2 → 3 → 4. The ten RQ deliverables are the canonical finding source; where a cluster paper and an RQ conflict, believe the RQ.

Reproduced via the eighty6 QCEW API; see `scripts/04_reproduce.py`.

| Paper | File | RQs | Inference |
|-------|------|-----|-----------|
| 1 Descriptive structure | `paper1_descriptive_structure.md` | RQ1, RQ2, RQ5 | Descriptive; RQ2 is within-area association |
| 2 Measurement / health | `paper2_measurement_health.md` | RQ3, RQ4 | Psychometric; no policy claims |
| 3 MW exposure | `paper3_mw_exposure.md` | RQ6 | Data quality; no outcome regressions |
| 4 Exposure and outcomes | `paper4_exposure_outcomes.md` | RQ7–RQ10 | Tier A association; Tier B designs failed the causal screen |

Short RQ abstracts live in `rq/`.

## Inference tiers (do not upgrade)

- **Descriptive** (RQ1, RQ5): document levels and paths. No policy merge.
- **Measurement** (RQ3, RQ4, RQ6): construct validity and exposure QA.
- **Association** (RQ2, RQ7, RQ10): net of first differences or two-way FE. Never “effect of.”
- **Design-based candidate** (RQ8, RQ9): event study and border pairs. RQ8 pre-trends fail (`causal_reading = false`), so RQ8–RQ10 use no causal verbs.
