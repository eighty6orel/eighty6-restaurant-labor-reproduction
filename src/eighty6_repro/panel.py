"""Wage/employment shares, employees-per-establishment, and FSR/LSR splits.

Identities (same area × year × quarter × ownership × size):

- wage_share_7225 = wage_7225 / wage_all
- emp_share_7225  = emp_7225 / emp_all
- epe_7225        = emp_7225 / est_7225

Restaurant 4-digit: NAICS 7225 from 2011+; 7221+7222 for 2001–2010.
Disclosure-suppressed cells are dropped before aggregation; they are never zero-filled.
"""

from __future__ import annotations

import polars as pl

from eighty6_repro.config import (
    AGGLVL_COUNTY_4,
    AGGLVL_COUNTY_6,
    AGGLVL_COUNTY_TOTAL,
    AGGLVL_STATE_4,
    AGGLVL_STATE_6,
    AGGLVL_STATE_TOTAL,
    AGGLVL_US_4,
    AGGLVL_US_6,
    AGGLVL_US_TOTAL,
    IND_ALL,
    IND_RESTAURANTS_4,
    LSR_OTHER_CODES,
)
from eighty6_repro.metrics import usable_qcew_rows
from eighty6_repro.mw import LOCAL_MW_COUNTY_FIPS


def _weighted_aww() -> pl.Expr:
    return (
        (pl.col("avg_wkly_wage").cast(pl.Float64) * pl.col("annual_avg_emplvl").cast(pl.Float64)).sum()
        / pl.col("annual_avg_emplvl").cast(pl.Float64).sum().replace(0, None)
    )


def _geo_slice(
    df: pl.DataFrame, *, total_agglvl: str, four_agglvl: str, six_agglvl: str
) -> pl.DataFrame:
    all_ind = usable_qcew_rows(
        df.filter((pl.col("industry_code") == IND_ALL) & (pl.col("agglvl_code") == total_agglvl))
    ).select(
        [
            "year",
            "qtr",
            "area_fips",
            "area_title",
            pl.col("annual_avg_emplvl").alias("emp_all"),
            pl.col("total_qtrly_wages").alias("wage_all"),
            pl.col("qtrly_estabs").alias("est_all"),
            pl.col("avg_wkly_wage").alias("aww_all"),
        ]
    )
    rest4 = (
        usable_qcew_rows(
            df.filter(
                pl.col("industry_code").is_in([IND_RESTAURANTS_4, "7221", "7222"])
                & (pl.col("agglvl_code") == four_agglvl)
            )
        )
        .group_by(["year", "qtr", "area_fips"])
        .agg(
            pl.col("annual_avg_emplvl").sum().alias("emp_7225"),
            pl.col("total_qtrly_wages").sum().alias("wage_7225"),
            pl.col("qtrly_estabs").sum().alias("est_7225"),
            _weighted_aww().alias("aww_7225"),
        )
    )
    fsr = usable_qcew_rows(
        df.filter(
            pl.col("industry_code").is_in(["722511", "722110"])
            & (pl.col("agglvl_code") == six_agglvl)
        )
    ).select(
        [
            "year",
            "qtr",
            "area_fips",
            pl.col("annual_avg_emplvl").alias("emp_fsr"),
            pl.col("total_qtrly_wages").alias("wage_fsr"),
            pl.col("qtrly_estabs").alias("est_fsr"),
            pl.col("avg_wkly_wage").alias("aww_fsr"),
        ]
    )
    lsr = (
        usable_qcew_rows(
            df.filter(
                pl.col("industry_code").is_in(list(LSR_OTHER_CODES))
                & (pl.col("agglvl_code") == six_agglvl)
            )
        )
        .group_by(["year", "qtr", "area_fips"])
        .agg(
            pl.col("annual_avg_emplvl").sum().alias("emp_lsr"),
            pl.col("total_qtrly_wages").sum().alias("wage_lsr"),
            pl.col("qtrly_estabs").sum().alias("est_lsr"),
            _weighted_aww().alias("aww_lsr"),
            pl.len().alias("n_lsr_cells"),
        )
    )
    panel = (
        all_ind.join(rest4, on=["year", "qtr", "area_fips"], how="left")
        .join(fsr, on=["year", "qtr", "area_fips"], how="left")
        .join(lsr, on=["year", "qtr", "area_fips"], how="left")
    )
    return panel.with_columns(
        (
            pl.col("wage_7225").cast(pl.Float64)
            / pl.col("wage_all").cast(pl.Float64).replace(0, None)
        ).alias("wage_share_7225"),
        (
            pl.col("emp_7225").cast(pl.Float64) / pl.col("emp_all").cast(pl.Float64).replace(0, None)
        ).alias("emp_share_7225"),
        (
            pl.col("wage_fsr").cast(pl.Float64) / pl.col("wage_all").cast(pl.Float64).replace(0, None)
        ).alias("wage_share_fsr"),
        (
            pl.col("emp_fsr").cast(pl.Float64) / pl.col("emp_all").cast(pl.Float64).replace(0, None)
        ).alias("emp_share_fsr"),
        (
            pl.col("wage_lsr").cast(pl.Float64) / pl.col("wage_all").cast(pl.Float64).replace(0, None)
        ).alias("wage_share_lsr"),
        (
            pl.col("emp_lsr").cast(pl.Float64) / pl.col("emp_all").cast(pl.Float64).replace(0, None)
        ).alias("emp_share_lsr"),
        (
            pl.col("emp_7225").cast(pl.Float64) / pl.col("est_7225").cast(pl.Float64).replace(0, None)
        ).alias("epe_7225"),
        (
            pl.col("emp_fsr").cast(pl.Float64) / pl.col("est_fsr").cast(pl.Float64).replace(0, None)
        ).alias("epe_fsr"),
        (
            pl.col("emp_lsr").cast(pl.Float64) / pl.col("est_lsr").cast(pl.Float64).replace(0, None)
        ).alias("epe_lsr"),
        pl.col("area_fips").str.slice(0, 2).alias("state_fips"),
        (pl.col("year") * 4 + pl.col("qtr")).alias("time_id"),
        pl.col("area_fips").is_in(list(LOCAL_MW_COUNTY_FIPS)).alias("local_mw_flag"),
    )


def county_panel(df: pl.DataFrame) -> pl.DataFrame:
    return _geo_slice(
        df,
        total_agglvl=AGGLVL_COUNTY_TOTAL,
        four_agglvl=AGGLVL_COUNTY_4,
        six_agglvl=AGGLVL_COUNTY_6,
    )


def state_panel(df: pl.DataFrame) -> pl.DataFrame:
    return _geo_slice(
        df, total_agglvl=AGGLVL_STATE_TOTAL, four_agglvl=AGGLVL_STATE_4, six_agglvl=AGGLVL_STATE_6
    )


def us_panel(df: pl.DataFrame) -> pl.DataFrame:
    return _geo_slice(
        df, total_agglvl=AGGLVL_US_TOTAL, four_agglvl=AGGLVL_US_4, six_agglvl=AGGLVL_US_6
    )


def cast_decimals(df: pl.DataFrame) -> pl.DataFrame:
    decs = [c for c, t in zip(df.columns, df.dtypes, strict=False) if "Decimal" in str(t)]
    if not decs:
        return df
    return df.with_columns([pl.col(c).cast(pl.Float64) for c in decs])


def merge_mw(panel: pl.DataFrame, mw: pl.DataFrame) -> pl.DataFrame:
    cols = [
        c
        for c in (
            "state_fips",
            "year",
            "qtr",
            "mw_nominal",
            "mw_real_2024usd",
            "real_pct_chg_4q",
            "d_mw_real",
            "has_tip_credit",
            "source",
        )
        if c in mw.columns
    ]
    return panel.join(mw.select(cols), on=["state_fips", "year", "qtr"], how="left").with_columns(
        (pl.col("mw_nominal") / (pl.col("aww_7225") / 40.0)).alias("kaitz_7225"),
        (pl.col("mw_nominal") / (pl.col("aww_all") / 40.0)).alias("kaitz_all"),
    )
