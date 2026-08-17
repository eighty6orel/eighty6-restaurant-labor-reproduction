# Paper 4 — Exposure and restaurant outcomes

Reproduced via the eighty6 QCEW API and the public MW panel; see `scripts/04_reproduce.py`. Covers **RQ7–RQ10**.

## Inference discipline

| RQ | Design | Language that is allowed |
|----|--------|--------------------------|
| RQ7 | County TWFE, `linearmodels.PanelOLS`, state-clustered SE | **Conditional association**, net of county and year-quarter FE. **Not an effect.** |
| RQ8 | Callaway–Sant’Anna on a state-year panel; event = first year with real 4q MW change ≥ 10% | Dynamic association. Pre-trends fail (2 of 8 pre cells \|t\| > 1.96). `causal_reading = false`. |
| RQ9 | Census cross-state county pairs; levels and 4q first-differenced gaps | Association. Not upgraded to causal because RQ8 failed. |
| RQ10 | Split-sample TWFE on FSR/LSR shares, epe, ln establishments | Association. RQ8 did not unlock causal heterogeneity. |

Primary sample: 2014–2025, **excluding 2020–2021**, private 7225, disclosure-dropped, rebuilt MW panel.

## Headline findings

- **RQ7.** ln real MW → ln restaurant employment: coef **−0.049** (SE 0.046, p = 0.284, n = 95,545) — imprecise null. ln AWW **+0.179** (SE 0.020). ln establishments **−0.119** (SE 0.053).
- **RQ8.** 19 treated states, 51 states, 510 state-years. CS overall ATT **−0.030** (SE 0.011). Pre-period cells with \|t\| > 1.96: **2 of 8**. Do not say “the effect of the minimum wage.”
- **RQ9.** 1,308 undirected cross-state adjacency pairs (Census `county_adjacency.txt`). corr(MW gap, ln-emp gap) levels **+0.098**; first-differenced **−0.036** (n = 21,400). Levels are not changes.
- **RQ10.** emp_share_fsr coef **−0.003** (SE 0.001); emp_share_lsr **−0.001** (SE 0.002, n.s.); epe_lsr **+1.317** (SE 0.628). Same ln-est coefficient as RQ7.

## Threats

Policy endogeneity is the lead threat. Area FE absorb time-invariant confounding only. Staggered TWFE limitations apply (Goodman-Bacon 2021; Callaway–Sant’Anna 2021). Local-ordinance counties stay in the primary sample.

## Figures

`output/figures/fig_twfe_coefs.png`, `fig_cs_eventstudy.png`, `fig_border_fd.png`, `fig_het_coefs.png`.
