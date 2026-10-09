"""Evaluate the reranker on the test split once (backtest at a later cutoff).

Rankers, all on the same test candidates (features from August only):
    floor     global popularity among the candidates (PRD floor stand-in)
    v0_rule   opened-next count, then reverse count, then views (PRD V0)
    model     hgb_log1p from modeling/model.joblib (no refit)
    hybrid    per-slice routing fixed from the train CV (03-train.md):
              model for long_tail and torso, V0 for new, dormant, head

Metrics against the FULL truth (truth_test: every September next page from
A, also pages no candidate rule found):
    query side, per q_slice: nDCG@5 (gain log1p(r), ideal from the full
        truth), recall@5, recall_w@5 (click-weighted), hit@5
    item side, per item_slice: recall@5 and recall_w@5 over the true next
        pages in that slice
    coverage: distinct recommended pages / catalog
    candidate recall (the ceiling): from build_dataset_stats.json
Paired bootstrap over queries (95%) for model - V0 and hybrid - V0.
Overfit: the same nDCG@5 on the train split, scored with the fitted model.

Scores per row go to <data>/modeling/test_scores.parquet (git-ignored), so
a metric change reruns only this script's metric part.

Run: uv run python3 modeling/evaluate.py   (from the project folder)
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import numpy as np
import polars as pl

from features import FEATURES, transform

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[2] / "data" / "wikipedia-clickstream" / "modeling"
SEED, K, N_BOOT = 42, 5, 1000
SLICES = ["new", "dormant", "long_tail", "torso", "head"]
MODEL_SLICES = {"long_tail", "torso"}  # from the train CV, never from test
T0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


def scores(df: pl.DataFrame, bundle: dict) -> pl.DataFrame:
    X = df.select(bundle["features"]).to_numpy().astype(float)
    model = bundle["model"].predict(X)
    v0 = ((df["log_n_ac"].exp() - 1) * 1e12 + (df["log_n_ca"].exp() - 1) * 1e6 + df["log_views_c"]).to_numpy()
    floor = np.where(df["cand_popular"].to_numpy() > 0, df["log_in_c"].to_numpy(), -1.0)
    hybrid = np.where(df["q_slice"].is_in(list(MODEL_SLICES)).to_numpy(),
                      # model scores sit on a different scale; rank within query, so mixing is safe
                      model, v0)
    return df.select("q", "item", "q_slice", "item_slice", "r").with_columns(
        floor=pl.Series(floor), v0_rule=pl.Series(v0), model=pl.Series(model), hybrid=pl.Series(hybrid)
    )


def top5(sc: pl.DataFrame, col: str) -> pl.DataFrame:
    return (
        sc.sort(["q", col, "item"], descending=[False, True, False])
        .group_by("q", maintain_order=True).head(K)
        .with_columns(pos=pl.int_range(pl.len()).over("q"))
        .select("q", "item", "pos")
    )


def query_side(top: pl.DataFrame, truth: pl.DataFrame, queries: pl.DataFrame) -> pl.DataFrame:
    t = truth.with_columns(gain=pl.col("r").cast(pl.Float64).log1p())
    ideal = (
        t.sort(["q", "gain"], descending=[False, True]).group_by("q", maintain_order=True).head(K)
        .with_columns(d=1.0 / (pl.int_range(pl.len()).over("q") + 2).cast(pl.Float64).log(2))
        .group_by("q").agg(idcg=(pl.col("gain") * pl.col("d")).sum())
    )
    tot = t.group_by("q").agg(n_true=pl.len(), R=pl.col("r").sum())
    hits = (
        top.join(t.select("q", "item", "r", "gain"), on=["q", "item"], how="inner")
        .with_columns(d=1.0 / (pl.col("pos") + 2).cast(pl.Float64).log(2))
        .group_by("q").agg(dcg=(pl.col("gain") * pl.col("d")).sum(), n_hit=pl.len(), r_hit=pl.col("r").sum())
    )
    return (
        queries.select("q", "q_slice").join(ideal, on="q").join(tot, on="q")
        .join(hits, on="q", how="left").with_columns(pl.col("dcg", "n_hit", "r_hit").fill_null(0))
        .select(
            "q", "q_slice",
            ndcg=pl.col("dcg") / pl.col("idcg"),
            recall=pl.col("n_hit") / pl.min_horizontal(pl.col("n_true"), pl.lit(K)),
            recall_w=pl.col("r_hit") / pl.col("R"),
            hit=(pl.col("n_hit") > 0).cast(pl.Float64),
        )
        .sort("q")
    )


def item_side(top: pl.DataFrame, truth: pl.DataFrame) -> pl.DataFrame:
    """Per (query, item_slice): true next pages, how many the top 5 showed."""
    t = truth.join(top.select("q", "item", shown=pl.lit(1)), on=["q", "item"], how="left").with_columns(
        pl.col("shown").fill_null(0)
    )
    return t.group_by("q", "item_slice").agg(
        n=pl.len(), n_shown=pl.col("shown").sum(), r=pl.col("r").sum(), r_shown=(pl.col("r") * pl.col("shown")).sum()
    )


def summarize(pq: pl.DataFrame, it: pl.DataFrame, w: dict) -> dict:
    out = {"query_side": {}, "item_side": {}}
    for m in ("ndcg", "recall", "recall_w", "hit"):
        by = {s: float(pq.filter(pl.col("q_slice") == s)[m].mean()) for s in SLICES}
        out["query_side"][m] = {"weighted": sum(w[s] * by[s] for s in SLICES), **by}
    agg = it.group_by("item_slice").agg(pl.col("n", "n_shown", "r", "r_shown").sum())
    for row in agg.iter_rows(named=True):
        out["item_side"][row["item_slice"]] = {
            "true_pairs": row["n"], "recall": row["n_shown"] / row["n"], "recall_w": row["r_shown"] / row["r"]
        }
    return out


def boot_query(pa: pl.DataFrame, pb: pl.DataFrame, w: dict, rng, metric: str = "ndcg") -> dict:
    j = pa.select("q", "q_slice", a=metric).join(pb.select("q", b=metric), on="q")
    res, draws = {}, {}
    for s in SLICES:
        d = j.filter(pl.col("q_slice") == s).select(pl.col("a") - pl.col("b")).to_series().to_numpy()
        draws[s] = d[rng.integers(0, len(d), (N_BOOT, len(d)))].mean(axis=1)
        res[s] = [round(float(d.mean()), 4), *[round(float(x), 4) for x in np.percentile(draws[s], [2.5, 97.5])]]
    wd = sum(w[s] * draws[s] for s in SLICES)
    res["weighted"] = [round(float(sum(w[s] * res[s][0] for s in SLICES)), 4),
                       *[round(float(x), 4) for x in np.percentile(wd, [2.5, 97.5])]]
    return res


def boot_item(ia: pl.DataFrame, ib: pl.DataFrame, rng) -> dict:
    """Item-side recall@5 delta per item_slice; resample queries (ratio estimator)."""
    res = {}
    for s in SLICES:
        a = ia.filter(pl.col("item_slice") == s).sort("q")
        b = ib.filter(pl.col("item_slice") == s).sort("q")
        if a.height == 0:
            continue
        n, sa, sb = a["n"].to_numpy(), a["n_shown"].to_numpy(), b["n_shown"].to_numpy()
        idx = rng.integers(0, len(n), (N_BOOT, len(n)))
        d = sa[idx].sum(1) / n[idx].sum(1) - sb[idx].sum(1) / n[idx].sum(1)
        res[s] = [round(float(sa.sum() / n.sum() - sb.sum() / n.sum()), 4),
                  *[round(float(x), 4) for x in np.percentile(d, [2.5, 97.5])]]
    return res


def evaluate_split(split: str, bundle: dict, rankers: list[str]) -> tuple[dict, dict, dict]:
    pairs = pl.read_parquet(OUT / f"pairs_{split}.parquet")
    df = transform(pairs, split)
    sc = scores(df, bundle)
    truth = pl.read_parquet(OUT / f"truth_{split}.parquet")
    queries = pl.read_parquet(OUT / f"queries_{split}.parquet")
    pq, it = {}, {}
    for r in rankers:
        top = top5(sc, r)
        pq[r] = query_side(top, truth, queries)
        it[r] = item_side(top, truth)
    return sc, pq, it


def main() -> None:
    bundle = joblib.load(HERE / "model.joblib")
    assert bundle["features"] == FEATURES
    stats = json.loads((HERE / "build_dataset_stats.json").read_text())
    pop = stats["test"]["population"]
    w = {s: pop[s] / sum(pop.values()) for s in SLICES}
    rankers = ["floor", "v0_rule", "model", "hybrid"]
    rng = np.random.default_rng(SEED)

    sc, pq, it = evaluate_split("test", bundle, rankers)
    sc.write_parquet(OUT / "test_scores.parquet")
    log(f"scored test: {sc.height:,} pairs, {sc['q'].n_unique():,} queries")
    catalog = pl.read_parquet(OUT / "titles.parquet").height

    res = {}
    for r in rankers:
        res[r] = summarize(pq[r], it[r], w)
        res[r]["coverage"] = top5(sc, r)["item"].n_unique() / catalog
        q = res[r]["query_side"]
        log(f"{r}: nDCG@5 weighted {q['ndcg']['weighted']:.4f} "
            + " ".join(f"{s} {q['ndcg'][s]:.3f}" for s in SLICES)
            + f" | recall_w@5 {q['recall_w']['weighted']:.4f}")
        log(f"{r}: item-side recall@5 " + " ".join(
            f"{s} {res[r]['item_side'][s]['recall']:.3f}" for s in SLICES if s in res[r]["item_side"]))

    ci = {
        "model - v0_rule": {m: boot_query(pq["model"], pq["v0_rule"], w, rng, m) for m in ("ndcg", "recall_w")},
        "hybrid - v0_rule": {m: boot_query(pq["hybrid"], pq["v0_rule"], w, rng, m) for m in ("ndcg", "recall_w")},
        "v0_rule - floor": {"ndcg": boot_query(pq["v0_rule"], pq["floor"], w, rng)},
        "item_side recall@5, model - v0_rule": boot_item(it["model"], it["v0_rule"], rng),
        "item_side recall@5, hybrid - v0_rule": boot_item(it["hybrid"], it["v0_rule"], rng),
    }
    for k_, v in ci.items():
        log(f"CI {k_}: {v}")

    # Overfit: same truth-based nDCG@5 on the train split, fitted model.
    _, pq_tr, _ = evaluate_split("train", bundle, ["model", "v0_rule"])
    tr_pop = stats["train"]["population"]
    w_tr = {s: tr_pop[s] / sum(tr_pop.values()) for s in SLICES}
    gap = {r: sum(w_tr[s] * float(pq_tr[r].filter(pl.col("q_slice") == s)["ndcg"].mean()) for s in SLICES)
           for r in ("model", "v0_rule")}
    log(f"train nDCG@5 weighted: model {gap['model']:.4f}, v0 {gap['v0_rule']:.4f}")

    out = {"rankers": res, "bootstrap": ci, "weights": w, "train_ndcg5_weighted": gap,
           "candidate_recall_test": {"query_side": stats["test"]["candidate_recall_query_side"],
                                     "item_side": stats["test"]["candidate_recall_item_side"]}}
    (HERE / "evaluate_results.json").write_text(json.dumps(out, indent=2))
    log("done")


if __name__ == "__main__":
    main()
