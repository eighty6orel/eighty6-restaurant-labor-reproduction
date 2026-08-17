"""Disclosure filter and measurement helpers."""

from __future__ import annotations

import numpy as np
import polars as pl

from eighty6_repro.config import DISCLOSURE_SUPPRESSED


def usable_qcew_rows(df: pl.DataFrame) -> pl.DataFrame:
    """Drop BLS non-disclosable rows. Never treat missing wages as zero."""
    return df.filter(
        (
            pl.col("disclosure_code").is_null()
            | (pl.col("disclosure_code") != DISCLOSURE_SUPPRESSED)
        )
        & pl.col("total_qtrly_wages").is_not_null()
        & pl.col("annual_avg_emplvl").is_not_null()
    )


def cronbach_alpha(x: np.ndarray) -> float:
    k = x.shape[1]
    if k < 2:
        return float("nan")
    item_var = x.var(axis=0, ddof=1)
    total_var = x.sum(axis=1).var(ddof=1)
    if total_var <= 0:
        return float("nan")
    return float((k / (k - 1)) * (1 - item_var.sum() / total_var))


def variance_decomp(s: pl.Series, group: pl.Series) -> dict[str, float | int | None]:
    """Between vs within share of variance (descriptive, not a random-effects model)."""
    df = pl.DataFrame({"y": s, "g": group}).drop_nulls()
    if df.height < 10:
        return {"between": None, "within": None, "n": df.height}
    overall = df["y"].var()
    means = df.group_by("g").agg(pl.col("y").mean().alias("m"), pl.len().alias("n"))
    between = means["m"].var()
    within = df.join(means, on="g").select((pl.col("y") - pl.col("m")).alias("e"))["e"].var()
    tot = (between or 0) + (within or 0)
    return {
        "between": float(between) if between is not None else None,
        "within": float(within) if within is not None else None,
        "between_share": float(between / tot) if tot else None,
        "within_share": float(within / tot) if tot else None,
        "overall": float(overall) if overall is not None else None,
        "n": df.height,
        "n_groups": means.height,
    }
