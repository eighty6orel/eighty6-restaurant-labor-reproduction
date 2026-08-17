# Paper 2 — Measurement: is “restaurant health” one dimension?

Reproduced via the eighty6 QCEW API; see `scripts/04_reproduce.py`. Covers **RQ3, RQ4**. Inference is psychometric. **No policy claims.**

## Question

Do wage share, employment share, average weekly wage, employees per establishment, and five-year establishment growth form a reliable one-number “health” index?

## Method

2024Q1 county complete cases on five items (n = 2,175 in the live panel). Items are z-scored. Cronbach’s α uses the standard k/(k−1) formula. PCA is on the correlation matrix; retain eigenvalue ≥ 1. Rank stability: Spearman of equal-weight composite vs PC1 vs wage-share-only, plus 200 bootstrap draws with N(0, 0.15) item noise.

## Headline findings

- **RQ3.** Cronbach’s α = **0.615** — below the conventional 0.70 screen.
- **RQ3.** Two eigenvalues ≥ 1. PC1 explains **0.455** of variance (mix: wage and employment shares); PC2 **0.219** (pay and establishment growth).
- **RQ4.** Equal-weight vs PC1 Spearman **0.941**; equal-weight vs wage-share-only **0.812**.
- **RQ4.** Median bootstrap rank-interval width **432** ranks on a 2,175-county list (P90 = 571). Rank gaps narrower than that width are ties.
- **RQ4.** Wage-share ranks 2014Q1 vs 2024Q1 Spearman **0.894** (n = 2,135): mix persists; that is not precision of a health score.

## Interpretation

A one-number restaurant “health” index is not supported. High wage share is not health — it is industry mix. Ranks are descriptive devices, never treatments.

## Figures

`output/figures/fig_pca_scree.png`, `fig_rank_width.png`.
