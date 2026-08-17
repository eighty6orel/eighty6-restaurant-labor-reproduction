"""RQ1–RQ10 estimators. Language matches the deliverables: no new causal claims."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from eighty6_repro.config import EVENT_REAL_PCT_THRESHOLD, INFERENCE_EXCLUDE_YEARS, PRIMARY_WINDOW
from eighty6_repro.figures import save_fig
from eighty6_repro.metrics import cronbach_alpha, variance_decomp
from eighty6_repro.paths import tables_dir


def _write_row(name: str, row: dict[str, Any]) -> None:
    dest = tables_dir() / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    flat = {k: (str(v) if isinstance(v, list | dict) else v) for k, v in row.items()}
    pl.DataFrame([flat]).write_csv(dest)


def primary_sample(county: pl.DataFrame) -> pl.DataFrame:
    y0, y1 = PRIMARY_WINDOW
    excl = INFERENCE_EXCLUDE_YEARS
    return county.filter(
        (pl.col("year") >= y0)
        & (pl.col("year") <= y1)
        & (~pl.col("year").is_in(list(excl)))
        & (pl.col("emp_7225") > 0)
        & (pl.col("mw_real_2024usd") > 0)
    ).with_columns(
        pl.col("emp_7225").log().alias("ln_emp"),
        pl.col("est_7225").log().alias("ln_est"),
        pl.col("aww_7225").log().alias("ln_aww"),
        pl.col("mw_real_2024usd").log().alias("ln_mw_real"),
        pl.col("epe_7225").log().alias("ln_epe"),
    )


def twfe(df: pl.DataFrame, y: str, x: str) -> dict[str, Any]:
    """linearmodels PanelOLS two-way FE, state-clustered SE. Conditional association."""
    from linearmodels.panel import PanelOLS

    pdf2 = df.select(["area_fips", "time_id", "state_fips", y, x]).drop_nulls().to_pandas()
    pdf2 = pdf2.set_index(["area_fips", "time_id"])
    if len(pdf2) < 80:
        return {"n": len(pdf2), "error": "too few rows", "outcome": y}
    try:
        res = PanelOLS(pdf2[y], pdf2[[x]], entity_effects=True, time_effects=True).fit(
            cov_type="clustered", clusters=pdf2["state_fips"]
        )
    except Exception:
        res = PanelOLS(pdf2[y], pdf2[[x]], entity_effects=True, time_effects=True).fit(
            cov_type="clustered", cluster_entity=True
        )
    return {
        "n": int(res.nobs),
        "coef": float(res.params[x]),
        "se": float(res.std_errors[x]),
        "t": float(res.tstats[x]),
        "p": float(res.pvalues[x]),
        "outcome": y,
        "estimator": "linearmodels.PanelOLS TWFE, state-clustered",
        "inference": "conditional association, not an effect",
    }


def rq01(us: pl.DataFrame, county: pl.DataFrame) -> dict[str, Any]:
    us_ts = us.sort(["year", "qtr"]).with_columns(
        (pl.col("year") + (pl.col("qtr") - 1) / 4).alias("t")
    )
    if us_ts.height and "wage_share_7225" in us_ts.columns:
        plt.figure(figsize=(8.2, 4.2))
        plt.plot(us_ts["t"], 100 * us_ts["wage_share_7225"], label="Wage-bill share", color="#1f4e79")
        plt.plot(us_ts["t"], 100 * us_ts["emp_share_7225"], label="Employment share", color="#c45911")
        plt.axvspan(2020, 2022, color="#ddd", alpha=0.6)
        plt.ylabel("Restaurant share of private all-industry (%)")
        plt.title("U.S. restaurant intensity, NAICS 7225 (descriptive)")
        plt.legend(frameon=False)
        save_fig("fig_us_shares.png")

    c24 = county.filter(
        (pl.col("year") == 2024) & (pl.col("qtr") == 1) & pl.col("wage_share_7225").is_not_null()
    )
    if c24.height:
        plt.figure(figsize=(7.2, 4.0))
        plt.hist(100 * c24["wage_share_7225"].to_numpy(), bins=20, color="#1f4e79", edgecolor="white")
        plt.xlabel("Wage-bill share 2024Q1 (%)")
        plt.ylabel("Counties")
        plt.title(f"Cross-county wage-share distribution (n={c24.height})")
        save_fig("fig_county_hist_2024q1.png")

    vdf = county.filter(
        (pl.col("year") >= 2014)
        & (pl.col("year") <= 2024)
        & pl.col("wage_share_7225").is_not_null()
    )
    decomp = (
        variance_decomp(vdf["wage_share_7225"], vdf["area_fips"]) if vdf.height else {}
    )
    us14 = us.filter((pl.col("year") == 2014) & (pl.col("qtr") == 1))
    us24 = us.filter((pl.col("year") == 2024) & (pl.col("qtr") == 1))

    def _first(frame: pl.DataFrame, col: str) -> float | None:
        if not frame.height or col not in frame.columns:
            return None
        val = frame[col][0]
        return None if val is None else float(val)

    out = {
        "us_2014q1_ws": _first(us14, "wage_share_7225"),
        "us_2024q1_ws": _first(us24, "wage_share_7225"),
        "us_2014q1_es": _first(us14, "emp_share_7225"),
        "us_2024q1_es": _first(us24, "emp_share_7225"),
        "county_n_2024q1": c24.height,
        "county_mean_ws": float(c24["wage_share_7225"].mean()) if c24.height else None,
        "county_p10": float(c24["wage_share_7225"].quantile(0.1)) if c24.height else None,
        "county_p50": float(c24["wage_share_7225"].quantile(0.5)) if c24.height else None,
        "county_p90": float(c24["wage_share_7225"].quantile(0.9)) if c24.height else None,
        "between_share": decomp.get("between_share"),
        "within_share": decomp.get("within_share"),
        "var_n": decomp.get("n"),
        "var_areas": decomp.get("n_groups"),
        "inference_tier": "descriptive",
    }
    _write_row("table_rq01_headlines.csv", out)
    return out


def rq02(county: pl.DataFrame) -> dict[str, Any]:
    d = (
        county.filter((pl.col("year") >= 2014) & (pl.col("year") <= 2024))
        .sort(["area_fips", "year", "qtr"])
        .with_columns(
            (pl.col("epe_7225") - pl.col("epe_7225").shift(4).over("area_fips")).alias("d_epe"),
            (pl.col("aww_7225") - pl.col("aww_7225").shift(4).over("area_fips")).alias("d_aww"),
            (pl.col("epe_fsr") - pl.col("epe_fsr").shift(4).over("area_fips")).alias("d_epe_fsr"),
            (pl.col("aww_fsr") - pl.col("aww_fsr").shift(4).over("area_fips")).alias("d_aww_fsr"),
            (pl.col("epe_lsr") - pl.col("epe_lsr").shift(4).over("area_fips")).alias("d_epe_lsr"),
            (pl.col("aww_lsr") - pl.col("aww_lsr").shift(4).over("area_fips")).alias("d_aww_lsr"),
        )
    )
    out: dict[str, Any] = {"inference_tier": "association"}
    for name, xc, yc in [
        ("all_7225", "d_epe", "d_aww"),
        ("fsr", "d_epe_fsr", "d_aww_fsr"),
        ("lsr", "d_epe_lsr", "d_aww_lsr"),
    ]:
        s = d.drop_nulls([xc, yc])
        if s.height < 5:
            out[name] = {"n": s.height, "pearson_r": None, "spearman": None}
            continue
        x, y = s[xc].to_numpy().astype(float), s[yc].to_numpy().astype(float)
        r, p = stats.pearsonr(x, y)
        rho, _ = stats.spearmanr(x, y)
        out[name] = {
            "n": int(len(x)),
            "pearson_r": float(r),
            "pearson_p": float(p),
            "spearman": float(rho),
        }
    s = d.drop_nulls(["d_epe", "d_aww"])
    if s.height:
        plt.figure(figsize=(6.8, 4.2))
        plt.scatter(
            s["d_epe"].to_numpy(), s["d_aww"].to_numpy(), s=12, alpha=0.4, color="#1f4e79"
        )
        plt.axhline(0, color="#888", lw=0.6)
        plt.axvline(0, color="#888", lw=0.6)
        plt.xlabel("Δ employees per establishment (4q)")
        plt.ylabel("Δ average weekly wage (4q)")
        plt.title("Within-county first differences, NAICS 7225 (association)")
        save_fig("fig_rq02_scatter.png")
    flat = {
        f"{k}_{kk}": vv for k, v in out.items() if isinstance(v, dict) for kk, vv in v.items()
    }
    _write_row("table_rq02.csv", flat)
    return out


def _health_items(county: pl.DataFrame) -> tuple[pl.DataFrame, list[str]]:
    snap = county.filter(
        (pl.col("year") == 2024)
        & (pl.col("qtr") == 1)
        & pl.col("wage_share_7225").is_not_null()
        & pl.col("emp_share_7225").is_not_null()
        & pl.col("epe_7225").is_not_null()
        & pl.col("aww_7225").is_not_null()
    )
    g19 = county.filter((pl.col("year") == 2019) & (pl.col("qtr") == 1)).select(
        ["area_fips", pl.col("est_7225").alias("est19")]
    )
    snap = snap.join(g19, on="area_fips", how="left").with_columns(
        ((pl.col("est_7225") - pl.col("est19")) / pl.col("est19")).alias("est_g_5y")
    )
    items = ["wage_share_7225", "emp_share_7225", "aww_7225", "epe_7225", "est_g_5y"]
    return snap.drop_nulls(items), items


def rq03(county: pl.DataFrame) -> dict[str, Any]:
    complete, items = _health_items(county)
    if complete.height < 8:
        return {"n": complete.height, "alpha": None, "inference_tier": "measurement"}
    X = complete.select(items).to_numpy().astype(float)
    Xs = StandardScaler().fit_transform(X)
    pca = PCA().fit(Xs)
    ev = pca.explained_variance_ratio_
    loads = pca.components_[: min(3, Xs.shape[1])].T
    plt.figure(figsize=(6.2, 3.8))
    plt.bar(range(1, min(6, len(ev) + 1)), ev[:5], color="#1f4e79")
    plt.axhline(1 / len(items), color="#c45911", ls="--")
    plt.xlabel("Principal component")
    plt.ylabel("Share of variance")
    plt.title("PCA of candidate health indicators, 2024Q1")
    save_fig("fig_pca_scree.png")
    return {
        "n": complete.height,
        "alpha": cronbach_alpha(Xs),
        "n_eigen_ge1": int((pca.explained_variance_ >= 1).sum()),
        "ev": [float(x) for x in ev[:5]],
        "loadings": [
            {
                "item": items[i],
                "pc1": float(loads[i, 0]) if loads.shape[1] > 0 else None,
                "pc2": float(loads[i, 1]) if loads.shape[1] > 1 else None,
            }
            for i in range(len(items))
        ],
        "inference_tier": "measurement",
    }


def rq04(county: pl.DataFrame, m3: dict[str, Any] | None = None) -> dict[str, Any]:
    complete, items = _health_items(county)
    if complete.height < 8:
        return {"n": complete.height, "inference_tier": "measurement"}
    X = StandardScaler().fit_transform(complete.select(items).to_numpy().astype(float))
    eq = X.mean(axis=1)
    pc1 = PCA().fit_transform(X)[:, 0]
    ws = complete["wage_share_7225"].to_numpy()
    rng = np.random.default_rng(86)
    widths = []
    for _ in range(200):
        score = (X + rng.normal(0, 0.15, size=X.shape)).mean(axis=1)
        widths.append(score.argsort().argsort())
    width = np.vstack(widths).max(0) - np.vstack(widths).min(0)
    a = county.filter((pl.col("year") == 2014) & (pl.col("qtr") == 1)).select(
        ["area_fips", pl.col("wage_share_7225").alias("ws14")]
    )
    b = county.filter((pl.col("year") == 2024) & (pl.col("qtr") == 1)).select(
        ["area_fips", pl.col("wage_share_7225").alias("ws24")]
    )
    both = a.join(b, on="area_fips").drop_nulls()
    rho_time = (
        float(stats.spearmanr(both["ws14"].to_numpy(), both["ws24"].to_numpy()).statistic)
        if both.height >= 5
        else None
    )
    plt.figure(figsize=(6.4, 4.0))
    plt.hist(width, bins=20, color="#1f4e79", edgecolor="white")
    plt.xlabel("Bootstrap rank interval width")
    plt.ylabel("Counties")
    plt.title("Rank instability under item perturbation")
    save_fig("fig_rank_width.png")
    out = {
        "n": complete.height,
        "spearman_eq_pc1": float(stats.spearmanr(eq, pc1).statistic),
        "spearman_eq_ws": float(stats.spearmanr(eq, ws).statistic),
        "median_width": float(np.median(width)),
        "p90_width": float(np.quantile(width, 0.9)),
        "spearman_ws_2014_2024": rho_time,
        "n_time": both.height,
        "alpha_ref": (m3 or {}).get("alpha"),
        "inference_tier": "measurement",
    }
    _write_row("table_rq04.csv", out)
    return out


def rq05(us: pl.DataFrame) -> dict[str, Any]:
    us_ts = us.sort(["year", "qtr"]).with_columns(
        (pl.col("year") + (pl.col("qtr") - 1) / 4).alias("t")
    )
    if us_ts.height and "emp_fsr" in us_ts.columns:
        plt.figure(figsize=(8.2, 4.2))
        plt.plot(us_ts["t"], us_ts["emp_fsr"], label="Full-service", color="#1f4e79")
        plt.plot(us_ts["t"], us_ts["emp_lsr"], label="Limited-service / other", color="#c45911")
        plt.axvspan(2020, 2022, color="#ddd", alpha=0.6)
        plt.ylabel("Private employment")
        plt.title("FSR vs LSR employment, U.S. (descriptive)")
        plt.legend(frameon=False)
        save_fig("fig_fsr_lsr_emp.png")

    def _val(year: int, qtr: int, col: str) -> float | None:
        s = us.filter((pl.col("year") == year) & (pl.col("qtr") == qtr))
        if not s.height or col not in s.columns or s[col][0] is None:
            return None
        return float(s[col][0])

    out = {
        "emp_fsr_2019q4": _val(2019, 4, "emp_fsr"),
        "emp_lsr_2019q4": _val(2019, 4, "emp_lsr"),
        "emp_fsr_2020q2": _val(2020, 2, "emp_fsr"),
        "emp_lsr_2020q2": _val(2020, 2, "emp_lsr"),
        "emp_fsr_2024q4": _val(2024, 4, "emp_fsr"),
        "emp_lsr_2024q4": _val(2024, 4, "emp_lsr"),
        "inference_tier": "descriptive",
    }
    if out["emp_fsr_2019q4"] and out["emp_fsr_2020q2"]:
        out["fsr_trough_pct"] = out["emp_fsr_2020q2"] / out["emp_fsr_2019q4"] - 1
        out["lsr_trough_pct"] = out["emp_lsr_2020q2"] / out["emp_lsr_2019q4"] - 1
        if out["emp_fsr_2024q4"]:
            out["fsr_2024_vs_2019"] = out["emp_fsr_2024q4"] / out["emp_fsr_2019q4"] - 1
            out["lsr_2024_vs_2019"] = out["emp_lsr_2024q4"] / out["emp_lsr_2019q4"] - 1
    _write_row("table_rq05.csv", out)
    return out


def rq06(county: pl.DataFrame, mw: pl.DataFrame) -> dict[str, Any]:
    m = county.filter((pl.col("year") >= 2014) & (pl.col("year") <= 2025))
    merged = m.filter(pl.col("mw_nominal").is_not_null()) if "mw_nominal" in m.columns else m.head(0)
    snap = merged.filter((pl.col("year") == 2024) & (pl.col("qtr") == 1)) if merged.height else merged
    k = (
        snap.filter(
            pl.col("kaitz_7225").is_not_null()
            & (pl.col("kaitz_7225") > 0)
            & (pl.col("kaitz_7225") < 2)
        )
        if snap.height and "kaitz_7225" in snap.columns
        else snap.head(0)
    )
    if k.height:
        plt.figure(figsize=(7.2, 4.0))
        plt.hist(k["kaitz_7225"].to_numpy(), bins=20, color="#1f4e79", edgecolor="white")
        plt.xlabel("Kaitz (state MW / implied hourly AWW)")
        plt.title(f"Restaurant Kaitz ratio, 2024Q1 (n={k.height})")
        save_fig("fig_kaitz.png")
    fl = mw.filter(pl.col("state_fips") == "12") if mw.height else mw
    fl23 = {
        f"q{int(r['qtr'])}": float(r["mw_nominal"])
        for r in fl.filter(pl.col("year") == 2023).to_dicts()
    }
    local_n = (
        merged.filter(pl.col("local_mw_flag")).select("area_fips").n_unique()
        if merged.height and "local_mw_flag" in merged.columns
        else 0
    )
    n_counties = merged.select("area_fips").n_unique() if merged.height else 0
    out = {
        "mw_rows": mw.height,
        "merge_rate": (merged.height / m.height) if m.height else None,
        "merge_miss": (m.height - merged.height) if m.height else None,
        "counties": n_counties,
        "local_n": local_n,
        "local_share": (local_n / n_counties) if n_counties else None,
        "mw_min_2024q1": float(snap["mw_nominal"].min()) if snap.height else None,
        "mw_max_2024q1": float(snap["mw_nominal"].max()) if snap.height else None,
        "kaitz_median": float(k["kaitz_7225"].median()) if k.height else None,
        "kaitz_p90": float(k["kaitz_7225"].quantile(0.9)) if k.height else None,
        "fl_2023": fl23,
        "source_years": [int(mw["year"].min()), int(mw["year"].max())] if mw.height else None,
        "inference_tier": "measurement",
    }
    _write_row("table_rq06.csv", out)
    return out


def rq07(d: pl.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {"inference_tier": "association"}
    for y in ["ln_emp", "ln_est", "ln_aww", "wage_share_7225", "emp_share_7225", "ln_epe"]:
        if y not in d.columns:
            out[y] = {"error": f"missing {y}"}
            continue
        try:
            out[y] = twfe(d, y, "ln_mw_real")
        except Exception as exc:
            out[y] = {"error": str(exc)}
    rows = [{**v, "model": k} for k, v in out.items() if isinstance(v, dict) and "coef" in v]
    if rows:
        pl.DataFrame(rows).write_csv(tables_dir() / "table_twfe.csv")
        plt.figure(figsize=(7.4, 4.2))
        yx = range(len(rows))
        plt.errorbar(
            [r["coef"] for r in rows],
            list(yx),
            xerr=[1.96 * r["se"] for r in rows],
            fmt="o",
            color="#1f4e79",
        )
        plt.axvline(0, color="#888", lw=0.8)
        plt.yticks(list(yx), [r["model"] for r in rows])
        plt.xlabel("Coef on ln real MW (95% state-clustered)")
        plt.title("Tier A TWFE — conditional association")
        save_fig("fig_twfe_coefs.png")
    return out


def rq08(state: pl.DataFrame) -> dict[str, Any]:
    """Callaway–Sant'Anna on a state-year panel; pre-trends decide causal language."""
    st = state.filter(
        (pl.col("year") >= 2014)
        & (pl.col("year") <= 2025)
        & (~pl.col("year").is_in(list(INFERENCE_EXCLUDE_YEARS)))
        & (pl.col("emp_7225") > 0)
        & pl.col("mw_real_2024usd").is_not_null()
    ).with_columns(pl.col("emp_7225").log().alias("ln_emp"))
    if not st.height:
        return {"events": 0, "cs_causal": False, "inference_tier": "design-based (failed screen)"}
    ann = st.group_by(["state_fips", "year"]).agg(
        pl.col("ln_emp").mean(),
        pl.col("mw_real_2024usd").mean(),
        pl.col("real_pct_chg_4q").max() if "real_pct_chg_4q" in st.columns else pl.lit(None),
    )
    first = (
        ann.filter(pl.col("real_pct_chg_4q") >= EVENT_REAL_PCT_THRESHOLD)
        .group_by("state_fips")
        .agg(pl.col("year").min().alias("g"))
    )
    ann = ann.join(first, on="state_fips", how="left").with_columns(pl.col("g").fill_null(0))
    pdf = ann.to_pandas()
    pdf["state_id"] = pdf["state_fips"].astype("category").cat.codes + 1
    out: dict[str, Any] = {
        "events": int(first.height),
        "n_states": int(pdf["state_fips"].nunique()),
        "n_rows": int(len(pdf)),
        "cs_causal": False,
        "inference_tier": "design-based (failed screen)",
        "language": "dynamic association; causal_reading=False unless pre-trends pass",
    }
    try:
        from csdid.att_gt import ATTgt

        att = ATTgt(
            yname="ln_emp",
            tname="year",
            idname="state_id",
            gname="g",
            data=pdf,
            panel=True,
            allow_unbalanced_panel=True,
            biters=200,
            clustervar="state_id",
        )
        att.fit(est_method="dr")
        att.aggte(typec="dynamic")
        dyn = att.atte
        recs = []
        if isinstance(dyn, dict):
            egt = dyn.get("egt") or dyn.get("e")
            atts = dyn.get("att_egt") or dyn.get("att")
            ses = dyn.get("se_egt") or dyn.get("se")
            egt_a = np.ravel(egt) if egt is not None else np.array([])
            att_a = np.ravel(atts) if atts is not None else np.array([])
            se_a = np.ravel(ses) if ses is not None else np.array([])
            n = min(len(egt_a), len(att_a), len(se_a) if len(se_a) else len(att_a))
            for i in range(n):
                se_i = float(se_a[i]) if i < len(se_a) else float("nan")
                recs.append({"e": int(egt_a[i]), "att": float(att_a[i]), "se": se_i})
            overall = dyn.get("overall_att") or dyn.get("overall.att")
            out["cs_overall_att"] = float(np.ravel(overall)[0]) if overall is not None else None
            ose = dyn.get("overall_se") or dyn.get("overall.se")
            out["cs_overall_se"] = float(np.ravel(ose)[0]) if ose is not None else None
        if recs:
            pl.DataFrame(recs).write_csv(tables_dir() / "table_cs_dynamic.csv")
            plt.figure(figsize=(8.0, 4.2))
            plt.axhline(0, color="#888", lw=0.8)
            plt.errorbar(
                [r["e"] for r in recs],
                [r["att"] for r in recs],
                yerr=[1.96 * r["se"] for r in recs],
                fmt="o-",
                color="#1f4e79",
            )
            plt.xlabel("Years relative to first ≥10% real MW increase")
            plt.ylabel("CS ATT, ln restaurant employment")
            plt.title("Callaway–Sant’Anna dynamic ATT (state panel)")
            save_fig("fig_cs_eventstudy.png")
            pre = [r for r in recs if r["e"] < 0]
            n_sig = sum(1 for r in pre if r["se"] > 0 and abs(r["att"] / r["se"]) > 1.96)
            out["cs_pre_n"] = len(pre)
            out["cs_pre_sig"] = n_sig
            out["cs_causal"] = n_sig == 0 and len(pre) > 0
            out["cs_terms"] = recs
            out["cs_ok"] = True
        else:
            raise RuntimeError("CS fit completed but dynamic ATT path was empty")
    except Exception as exc:
        out["cs_ok"] = False
        out["cs_error"] = str(exc)
        out["cs_causal"] = False
    return out


def rq09(county: pl.DataFrame, *, download_adj: bool = True) -> dict[str, Any]:
    from eighty6_repro.adjacency import download_adjacency, parse_adjacency

    if download_adj:
        try:
            download_adjacency()
            adj = parse_adjacency().filter(pl.col("cross_state"))
        except Exception as exc:
            return {
                "error": f"adjacency unavailable: {exc}",
                "inference_tier": "design-based (association)",
            }
    else:
        return {"error": "adjacency download disabled", "inference_tier": "design-based (association)"}

    d = primary_sample(county)
    if not d.height:
        return {
            "adj_cross_state_pairs": adj.height,
            "pair_quarters": 0,
            "inference_tier": "design-based (association)",
        }
    a = d.select(
        [
            pl.col("area_fips").alias("fips_a"),
            "year",
            "qtr",
            pl.col("ln_emp").alias("ln_a"),
            pl.col("mw_real_2024usd").alias("mw_a"),
        ]
    )
    b = d.select(
        [
            pl.col("area_fips").alias("fips_b"),
            "year",
            "qtr",
            pl.col("ln_emp").alias("ln_b"),
            pl.col("mw_real_2024usd").alias("mw_b"),
        ]
    )
    pairs = adj.join(a, on="fips_a").join(b, on=["fips_b", "year", "qtr"])
    pairs = pairs.with_columns(
        (pl.col("mw_a") - pl.col("mw_b")).alias("dmw"),
        (pl.col("ln_a") - pl.col("ln_b")).alias("dln"),
    ).filter(pl.col("dmw").abs() > 1e-6)
    pairs = pairs.filter(pl.col("dln").is_finite() & pl.col("dmw").is_finite())
    fd = (
        pairs.sort(["fips_a", "fips_b", "year", "qtr"])
        .with_columns(
            (pl.col("dmw") - pl.col("dmw").shift(4).over(["fips_a", "fips_b"])).alias("ddmw"),
            (pl.col("dln") - pl.col("dln").shift(4).over(["fips_a", "fips_b"])).alias("ddln"),
        )
        .drop_nulls(["ddmw", "ddln"])
    )
    r, p = (
        stats.pearsonr(pairs["dmw"].to_numpy(), pairs["dln"].to_numpy())
        if pairs.height > 20
        else (None, None)
    )
    rr, pp = (
        stats.pearsonr(fd["ddmw"].to_numpy(), fd["ddln"].to_numpy())
        if fd.height > 20
        else (None, None)
    )
    if fd.height:
        samp = fd.sample(n=min(4000, fd.height), seed=86)
        plt.figure(figsize=(6.6, 4.2))
        plt.scatter(samp["ddmw"].to_numpy(), samp["ddln"].to_numpy(), s=8, alpha=0.3, color="#1f4e79")
        plt.axhline(0, color="#888", lw=0.6)
        plt.axvline(0, color="#888", lw=0.6)
        plt.xlabel("Δ (MW gap), 4q")
        plt.ylabel("Δ (ln emp gap), 4q")
        plt.title("Cross-border county pairs, first-differenced gaps")
        save_fig("fig_border_fd.png")
    out = {
        "adj_cross_state_pairs": adj.height,
        "pair_quarters": pairs.height,
        "pair_counties": pairs.select(["fips_a", "fips_b"]).n_unique() if pairs.height else 0,
        "corr_levels": float(r) if r is not None else None,
        "p_levels": float(p) if p is not None else None,
        "fd_n": fd.height,
        "corr_fd": float(rr) if rr is not None else None,
        "p_fd": float(pp) if pp is not None else None,
        "inference_tier": "design-based (association)",
        "language": "not upgraded to causal; RQ8 screen failed",
    }
    _write_row("table_rq09.csv", out)
    return out


def rq10(d: pl.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {"inference_tier": "association"}
    for y in ["emp_share_fsr", "emp_share_lsr", "epe_fsr", "epe_lsr", "ln_est"]:
        if y not in d.columns:
            out[y] = {"error": f"missing {y}"}
            continue
        try:
            out[y] = twfe(d, y, "ln_mw_real")
        except Exception as exc:
            out[y] = {"error": str(exc)}
    rows = [{**v, "model": k} for k, v in out.items() if isinstance(v, dict) and "coef" in v]
    if rows:
        pl.DataFrame(rows).write_csv(tables_dir() / "table_het_twfe.csv")
        plt.figure(figsize=(7.2, 3.8))
        plt.errorbar(
            [r["coef"] for r in rows],
            range(len(rows)),
            xerr=[1.96 * r["se"] for r in rows],
            fmt="o",
        )
        plt.yticks(range(len(rows)), [r["model"] for r in rows])
        plt.axvline(0, color="#888")
        plt.title("FSR/LSR and structure — TWFE on ln real MW (association)")
        save_fig("fig_het_coefs.png")
    return out
