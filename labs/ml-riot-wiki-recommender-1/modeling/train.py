"""Train the page-to-page reranker (Quick POC) on the train split only.

Candidates, all scored on the same 3-fold CV grouped by query:
    v0_rule          the PRD baseline, no fit: opened-next count, then the
                     reverse count, then views (proxy of V0)
    ridge_log1p      the simplest learned model: ridge on standardized
                     features + missing flags, target log1p(r)
    hgb_log1p        GBDT, squared error on log1p(r)      (design default)
    hgb_poisson_raw  GBDT, Poisson loss on raw r          (label sweep)
    hgb_sqrt         GBDT, squared error on sqrt(r)       (label sweep)
    hgb_share        GBDT, squared error on r / R(A)      (label sweep)
LambdaMART on 0-4 grades is not run: LightGBM needs the system libomp.

Metrics per query: nDCG@5 with gain log1p(r) for every candidate (fixed, so
labels compare), and recall_w@5 against all true next pages (truth_train).
Bootstrap CIs over queries on out-of-fold scores. The selected config is
then fit on every train row and saved to modeling/model.joblib.

Run: uv run python3 modeling/train.py   (from the project folder)
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from features import FEATURES

HERE = Path(__file__).resolve().parent
SANDBOX = HERE.parents[2]
OUT = SANDBOX / "data" / "wikipedia-clickstream" / "modeling"
SEED, K, FOLDS, CV_QUERY_SHARE, N_BOOT = 42, 5, 3, 0.5, 1000
SLICES = ["new", "dormant", "long_tail", "torso", "head"]
HGB = dict(max_iter=100, learning_rate=0.1, max_leaf_nodes=31, min_samples_leaf=100,
           l2_regularization=0.0, early_stopping=False, random_state=SEED)
TRACKER = SANDBOX / ".agents/skills/personal/ml-modeling/scripts/experiment_tracker.py"
T0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Targets and models
# ---------------------------------------------------------------------------
def target(df: pl.DataFrame, kind: str) -> np.ndarray:
    r = df["r"].cast(pl.Float64)
    if kind == "log1p":
        return r.log1p().to_numpy()
    if kind == "raw":
        return r.to_numpy()
    if kind == "sqrt":
        return r.sqrt().to_numpy()
    if kind == "share":  # share of A's label-month readers (all true next pages)
        return (df["r"] / df["R_q"]).fill_nan(0).to_numpy()
    raise ValueError(kind)


def linear_matrix(df: pl.DataFrame) -> np.ndarray:
    """Nulls -> 0 plus a missing flag, for the linear model only."""
    nullable = ["rank_ac", "is_link_ac", "item_age_days", "q_age_days"]
    cols = [pl.col(f).fill_null(0).alias(f) for f in FEATURES]
    flags = [pl.col(f).is_null().cast(pl.Float64).alias(f"{f}_missing") for f in nullable]
    return df.select(cols + flags).to_numpy().astype(float)


CANDIDATES = {
    "v0_rule": dict(kind="rule"),
    "ridge_log1p": dict(kind="ridge", target="log1p"),
    "hgb_log1p": dict(kind="hgb", target="log1p", loss="squared_error"),
    "hgb_poisson_raw": dict(kind="hgb", target="raw", loss="poisson"),
    "hgb_sqrt": dict(kind="hgb", target="sqrt", loss="squared_error"),
    "hgb_share": dict(kind="hgb", target="share", loss="squared_error"),
}


def fit_predict(cfg: dict, tr: pl.DataFrame, te: pl.DataFrame):
    if cfg["kind"] == "rule":
        s = (te["log_n_ac"].exp() - 1) * 1e12 + (te["log_n_ca"].exp() - 1) * 1e6 + te["log_views_c"]
        return None, s.to_numpy()
    y = target(tr, cfg["target"])
    if cfg["kind"] == "ridge":
        m = make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(linear_matrix(tr), y)
        return m, m.predict(linear_matrix(te))
    m = HistGradientBoostingRegressor(loss=cfg["loss"], **HGB)
    m.fit(tr.select(FEATURES).to_numpy().astype(float), y)
    return m, m.predict(te.select(FEATURES).to_numpy().astype(float))


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def per_query(df: pl.DataFrame, score: np.ndarray) -> pl.DataFrame:
    """nDCG@5 (gain log1p(r), ideal over the candidates) and recall_w@5
    (clicks in the top 5 / all label-month clicks from A)."""
    d = df.select("q", "q_slice", "label", "r", "R_q").with_columns(s=pl.Series(score))
    disc = 1.0 / (pl.int_range(pl.len()).over("q") + 2).cast(pl.Float64).log(2)
    top = (
        d.sort(["q", "s"], descending=[False, True]).group_by("q", maintain_order=True).head(K)
        .with_columns(g=pl.col("label") * disc)
        .group_by("q").agg(dcg=pl.col("g").sum(), r5=pl.col("r").sum())
    )
    ideal = (
        d.sort(["q", "label"], descending=[False, True]).group_by("q", maintain_order=True).head(K)
        .with_columns(g=pl.col("label") * disc)
        .group_by("q").agg(idcg=pl.col("g").sum(), q_slice=pl.col("q_slice").first(), R_q=pl.col("R_q").first())
    )
    return ideal.join(top, on="q").select(
        "q", "q_slice",
        ndcg=pl.when(pl.col("idcg") > 0).then(pl.col("dcg") / pl.col("idcg")).otherwise(0.0),
        recall_w=pl.when(pl.col("R_q") > 0).then(pl.col("r5") / pl.col("R_q")).otherwise(0.0),
    ).sort("q")


def summarize(pq: pl.DataFrame, w: dict) -> dict:
    out = {}
    for m in ("ndcg", "recall_w"):
        by = {s: pq.filter(pl.col("q_slice") == s)[m].mean() for s in SLICES}
        out[m] = {"weighted": sum(w[s] * by[s] for s in SLICES), **by}
    return out


def bootstrap(pa: pl.DataFrame, pb: pl.DataFrame, w: dict, rng) -> dict:
    """Paired bootstrap over queries (within slice) of mean(a) - mean(b), nDCG@5."""
    j = pa.select("q", "q_slice", a="ndcg").join(pb.select("q", b="ndcg"), on="q")
    res, draws = {}, {}
    for s in SLICES:
        dlt = j.filter(pl.col("q_slice") == s).select(pl.col("a") - pl.col("b")).to_series().to_numpy()
        idx = rng.integers(0, len(dlt), (N_BOOT, len(dlt)))
        draws[s] = dlt[idx].mean(axis=1)
        res[s] = [round(float(dlt.mean()), 4), *[round(float(x), 4) for x in np.percentile(draws[s], [2.5, 97.5])]]
    wd = sum(w[s] * draws[s] for s in SLICES)
    res["weighted"] = [round(float(sum(w[s] * res[s][0] for s in SLICES)), 4),
                       *[round(float(x), 4) for x in np.percentile(wd, [2.5, 97.5])]]
    return res


def track(name: str, params: dict, metrics: dict) -> None:
    subprocess.run(
        ["python3", str(TRACKER), "--log-file", str(HERE / "experiments.json"), "log",
         "--name", name, "--params", json.dumps(params), "--metrics", json.dumps(metrics)],
        check=True, capture_output=True,
    )


# ---------------------------------------------------------------------------
def main() -> None:
    stats = json.loads((HERE / "build_dataset_stats.json").read_text())["train"]
    pop = stats["population"]
    w = {s: pop[s] / sum(pop.values()) for s in SLICES}
    truth_R = pl.read_parquet(OUT / "truth_train.parquet").group_by("q").agg(R_q=pl.col("r").sum())
    df = pl.read_parquet(OUT / "features_train.parquet").join(truth_R, on="q", how="left").with_columns(
        pl.col("R_q").fill_null(0)
    )

    rng = np.random.default_rng(SEED)
    qs = df.select("q").unique().sort("q")
    cv_q = qs.filter(pl.Series(rng.random(qs.height) < CV_QUERY_SHARE))
    cv = df.join(cv_q, on="q", how="semi").sort(["q", "item"])
    groups = cv["q"].to_numpy()
    log(f"CV: {cv_q.height:,} queries ({CV_QUERY_SHARE:.0%}), {cv.height:,} rows, {FOLDS} folds by query")

    results, oof_pq = {}, {}
    for name, cfg in CANDIDATES.items():
        t = time.time()
        oof = np.zeros(cv.height)
        for k, (tr_i, te_i) in enumerate(GroupKFold(n_splits=FOLDS).split(cv, groups=groups)):
            _, oof[te_i] = fit_predict(cfg, cv[tr_i], cv[te_i])
        secs = time.time() - t
        pq = per_query(cv, oof)
        oof_pq[name] = pq
        summ = summarize(pq, w)
        results[name] = {"config": cfg, "cv_seconds": round(secs, 1), **summ}
        cv.select("q", "item").with_columns(score=pl.Series(oof)).write_parquet(OUT / f"oof_{name}.parquet")
        params = {**cfg, **(HGB if cfg["kind"] == "hgb" else {}), "folds": FOLDS, "cv_query_share": CV_QUERY_SHARE}
        track(name, params, {"ndcg5_weighted": round(summ["ndcg"]["weighted"], 4),
                             "recall_w5_weighted": round(summ["recall_w"]["weighted"], 4), "cv_seconds": round(secs, 1)})
        log(f"{name}: nDCG@5 weighted {summ['ndcg']['weighted']:.4f} "
            + " ".join(f"{s} {summ['ndcg'][s]:.3f}" for s in SLICES) + f" ({secs:.0f}s)")

    ci = {}
    for name in CANDIDATES:
        if name != "v0_rule":
            ci[f"{name} - v0_rule"] = bootstrap(oof_pq[name], oof_pq["v0_rule"], w, rng)
        if name.startswith("hgb_") and name != "hgb_log1p":
            ci[f"{name} - hgb_log1p"] = bootstrap(oof_pq[name], oof_pq["hgb_log1p"], w, rng)
    ci["hgb_log1p - ridge_log1p"] = bootstrap(oof_pq["hgb_log1p"], oof_pq["ridge_log1p"], w, rng)
    for k_, v in ci.items():
        log(f"CI {k_}: {v}")

    # Label sweep rule (design/high-level.md, Open items): a label replaces
    # log1p only if it wins on new and long_tail with CIs above 0 and does
    # not lose overall (weighted CI upper bound >= 0).
    chosen = "hgb_log1p"
    for name in ("hgb_poisson_raw", "hgb_sqrt", "hgb_share"):
        c = ci[f"{name} - hgb_log1p"]
        if c["new"][1] > 0 and c["long_tail"][1] > 0 and c["weighted"][2] >= 0:
            if chosen == "hgb_log1p" or results[name]["ndcg"]["weighted"] > results[chosen]["ndcg"]["weighted"]:
                chosen = name
    log(f"selected: {chosen}")

    t = time.time()
    model, _ = fit_predict(CANDIDATES[chosen], df, df.head(1))
    fit_secs = time.time() - t
    joblib.dump({"model": model, "features": FEATURES, "config": CANDIDATES[chosen], "params": HGB,
                 "threshold": None, "trained_on": "features_train.parquet (all rows)"},
                HERE / "model.joblib")
    log(f"final fit on {df.height:,} rows in {fit_secs:.0f}s -> modeling/model.joblib")

    out = {"weights": w, "cv": {"queries": cv_q.height, "rows": cv.height, "folds": FOLDS},
           "results": results, "bootstrap_ndcg5_delta": ci, "selected": chosen,
           "final_fit_seconds": round(fit_secs, 1), "final_rows": df.height}
    (HERE / "train_results.json").write_text(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
