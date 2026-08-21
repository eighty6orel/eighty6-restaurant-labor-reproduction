# Research generations

This repository reconstructs published restaurant-labor results from the eighty6 QCEW API. **Each generation is a dated folder.** Do not mix numbers across generations.

| ID | Folder | Unit | What a stranger can rebuild |
|----|--------|------|-----------------------------|
| county-20260816 | [`papers/`](../papers/) plus `scripts/` | County (and U.S. national) | RQ1–RQ10 headlines via `scripts/04_reproduce.py` |
| citygen-20260818 | [`20260818-citygen/`](20260818-citygen/) | 100 largest CBSAs | County cells aggregated to metros; shares recomputed from sums |

## Rules

1. Cite the **generation ID** with every number.
2. City shares are **recomputed from summed county numerators and denominators**. Averaging county shares is a bug.
3. Causal verbs stay gated on the pre-specified screen in that generation. The county event-study screen failed; do not upgrade language here.
