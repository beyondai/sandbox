#!/usr/bin/env python3
"""Monkey-mode baseline: "related article" recommender on Wikipedia Clickstream.

Proxy for the Riot internal-wiki recommender. Given the current article A,
rank the next articles C a reader will open.

Pipeline (seed 42, deterministic):
  1. Load enwiki clickstream 2026-09, keep article-to-article rows
     (type link/other), drop self pairs and Main_Page as a source.
  2. Thin every pair: h ~ Binomial(n, 7/30) is "history" (one week),
     t = n - h is "truth" (rest of the month).
  3. Queries = source articles, bucketed by history out-clicks
     (cold 0 / tail 1-50 / torso 51-1000 / head >1000). Disjoint, stratified
     train (~100k, 10% held out as val) and eval (~50k) query samples.
  4. Models: B0 popularity, B1 co-visitation (min_h / alpha sweep on val),
     ML reranker (HistGradientBoosting over click-graph candidates).
  5. Metrics: nDCG@10 (gain log1p(t)), recall@10 (set and click-weighted),
     hit@10, coverage; overall (population-weighted over buckets) and per
     bucket; stratified bootstrap CIs on reranker - B1; permutation
     importance.
  Additions beyond the plan (plan versions are kept and reported first):
     - Reranker-graded: same candidates/features, HGB regressor on log1p(t)
       instead of the binary t>0 label.
     - Hybrid: B1 for sources with history, Reranker for cold sources.
     - Novel-pair slice: truth restricted to pairs with h == 0 (targets the
       history never showed from A), the "discovery" case.

Run from the sandbox:  uv run python3 labs/ml-riot-wiki-recommender-1/monkey-mode/baseline.py
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

SEED = 42
P_HIST = 7 / 30
K = 10
BUCKETS = ["cold", "tail", "torso", "head"]
N_TRAIN, N_EVAL = 100_000, 50_000
MIN_TRAIN_PER_BUCKET, MIN_EVAL_PER_BUCKET = 10_000, 5_000
MIN_H_GRID = [1, 2, 3, 5, 10]
ALPHA_GRID = [0, 1, 5, 20, 100]
MAX_TRAIN_ROWS = 6_000_000
N_BOOT = 1000
PERM_QUERIES = 5_000

HERE = Path(__file__).resolve().parent
SANDBOX = HERE.parents[2]
DATA = SANDBOX / "data" / "wikipedia-clickstream"
RAW = DATA / "clickstream-enwiki-2026-09.tsv.gz"

FEATURES = [
    "h_ac",  # h(A,C) history clicks A -> C
    "p_c_given_a",  # h(A,C) / H(A)
    "b1_rank",  # rank of C among A's history out-edges (by h)
    "twohop",  # sum_B P(B|A) P(C|B)
    "rev_h",  # h(C,A) reverse edge
    "in_c",  # C's history in-clicks
    "out_c",  # C's history out-clicks
    "out_a",  # A's history out-clicks
    "pair_type",  # 0 link, 1 other, NaN if no history pair
    "n_sources",  # how many candidate generators produced C
]

T0 = time.time()
LOG: list[str] = []


def log(msg: str) -> None:
    line = f"[{time.time() - T0:7.1f}s] {msg}"
    print(line, flush=True)
    LOG.append(line)


# --------------------------------------------------------------------------
# 1-2. Load, filter, thin
# --------------------------------------------------------------------------
def load_and_thin() -> tuple[pl.DataFrame, dict]:
    stats: dict = {}
    raw = pl.read_csv(
        RAW,
        separator="\t",
        has_header=False,
        quote_char=None,
        schema={"prev": pl.String, "curr": pl.String, "type": pl.String, "n": pl.Int64},
    )
    stats["raw_rows"] = raw.height
    stats["raw_clicks"] = int(raw["n"].sum())
    stats["raw_rows_by_type"] = {
        r["type"]: r["len"] for r in raw.group_by("type").len().sort("type").iter_rows(named=True)
    }
    log(f"raw rows={raw.height:,} by type={stats['raw_rows_by_type']}")

    df = raw.filter(
        pl.col("type").is_in(["link", "other"])
        & (pl.col("prev") != pl.col("curr"))
        & (pl.col("prev") != "Main_Page")
    )
    del raw
    stats["filtered_rows"] = df.height
    stats["filtered_clicks"] = int(df["n"].sum())
    log(f"filtered rows={df.height:,} clicks={stats['filtered_clicks']:,}")

    # Thinning in file order (filter preserves order), seed 42.
    rng = np.random.default_rng(SEED)
    n = df["n"].to_numpy()
    h = rng.binomial(n, P_HIST).astype(np.int64)
    df = df.with_columns(h=pl.Series(h), t=pl.Series(n - h))
    stats["thin_ratio"] = float(h.sum() / n.sum())
    log(f"thinning: sum(h)/sum(n) = {stats['thin_ratio']:.5f} (target {P_HIST:.5f})")

    titles = (
        pl.concat([df.select(title="prev"), df.select(title="curr")])
        .unique()
        .sort("title")
        .with_row_index("id")
        .with_columns(pl.col("id").cast(pl.Int32))
    )
    stats["catalog_articles"] = titles.height
    pairs = (
        df.join(titles.rename({"title": "prev", "id": "src"}), on="prev")
        .join(titles.rename({"title": "curr", "id": "dst"}), on="curr")
        .select(
            "src",
            "dst",
            pl.when(pl.col("type") == "link").then(0).otherwise(1).cast(pl.Int8).alias("type"),
            "n",
            "h",
            "t",
        )
        .sort(["src", "dst"])
    )
    assert pairs.height == df.height, "id join dropped rows"
    pairs.write_parquet(DATA / "pairs_thinned_seed42.parquet")
    titles.write_parquet(DATA / "titles.parquet")
    stats["hist_rows"] = int((pairs["h"] > 0).sum())
    stats["truth_rows"] = int((pairs["t"] > 0).sum())
    log(
        f"catalog={titles.height:,} hist rows={stats['hist_rows']:,} "
        f"truth rows={stats['truth_rows']:,}"
    )
    return pairs, stats, titles


# --------------------------------------------------------------------------
# 3. Queries and buckets
# --------------------------------------------------------------------------
def bucket_expr(col: str) -> pl.Expr:
    c = pl.col(col)
    return (
        pl.when(c == 0)
        .then(pl.lit("cold"))
        .when(c <= 50)
        .then(pl.lit("tail"))
        .when(c <= 1000)
        .then(pl.lit("torso"))
        .otherwise(pl.lit("head"))
    )


def sample_queries(truth: pl.DataFrame, out_h: pl.DataFrame, stats: dict):
    sources = (
        truth.select(q="src")
        .unique()
        .join(out_h.rename({"src": "q"}), on="q", how="left")
        .with_columns(pl.col("H").fill_null(0))
        .with_columns(bucket=bucket_expr("H"))
        .sort("q")
    )
    pop = {r["bucket"]: r["len"] for r in sources.group_by("bucket").len().iter_rows(named=True)}
    total = sum(pop.values())
    weights = {b: pop.get(b, 0) / total for b in BUCKETS}
    stats["source_population"] = {b: pop.get(b, 0) for b in BUCKETS}
    stats["source_population_total"] = total
    stats["bucket_weights"] = weights
    log(f"eligible sources (have truth) = {total:,}; per bucket {stats['source_population']}")

    rng = np.random.default_rng(SEED)
    ev, tr = [], []
    for b in BUCKETS:
        ids = sources.filter(pl.col("bucket") == b)["q"].to_numpy()
        ids = ids[rng.permutation(len(ids))]
        n_ev = min(max(MIN_EVAL_PER_BUCKET, round(N_EVAL * weights[b])), len(ids) // 3)
        n_tr = min(max(MIN_TRAIN_PER_BUCKET, round(N_TRAIN * weights[b])), len(ids) - n_ev)
        ev.append(pl.DataFrame({"q": ids[:n_ev], "bucket": [b] * n_ev}))
        tr.append(pl.DataFrame({"q": ids[n_ev : n_ev + n_tr], "bucket": [b] * n_tr}))
    ev_q = pl.concat(ev).with_columns(pl.col("q").cast(pl.Int32))
    tr_q = pl.concat(tr).with_columns(pl.col("q").cast(pl.Int32))
    assert ev_q.join(tr_q, on="q").height == 0, "train/eval query overlap"
    log(f"assert ok: train ({tr_q.height:,}) and eval ({ev_q.height:,}) query sets are disjoint")
    perm = rng.permutation(tr_q.height)
    is_val = np.zeros(tr_q.height, dtype=bool)
    is_val[perm[: tr_q.height // 10]] = True
    tr_q = tr_q.with_columns(is_val=pl.Series(is_val))
    val_q = tr_q.filter("is_val").drop("is_val")
    fit_q = tr_q.filter(~pl.col("is_val")).drop("is_val")
    for name, f in [("eval", ev_q), ("train_fit", fit_q), ("val", val_q)]:
        cnt = {r["bucket"]: r["len"] for r in f.group_by("bucket").len().iter_rows(named=True)}
        stats[f"n_{name}_queries"] = {b: cnt.get(b, 0) for b in BUCKETS}
        log(f"{name} queries: {f.height:,} {stats[f'n_{name}_queries']}")
    return ev_q, fit_q, val_q


# --------------------------------------------------------------------------
# Helpers: top-k per group
# --------------------------------------------------------------------------
def topk(df: pl.DataFrame, group: str, by: list[str], desc: list[bool], k: int, rank="rank"):
    return (
        df.sort([group, *by], descending=[False, *desc])
        .with_columns((pl.int_range(pl.len()).over(group) + 1).alias(rank))
        .filter(pl.col(rank) <= k)
    )


# --------------------------------------------------------------------------
# 4. Models (history only)
# --------------------------------------------------------------------------
class History:
    """Everything here is derived from history counts h only."""

    def __init__(self, hist: pl.DataFrame):
        assert set(hist.columns) == {"src", "dst", "type", "h"}, hist.columns
        assert "t" not in hist.columns
        self.edges = hist
        self.out_h = hist.group_by("src").agg(H=pl.col("h").sum())
        self.in_h = hist.group_by("dst").agg(in_h=pl.col("h").sum())
        total = int(hist["h"].sum())
        self.pop = (
            self.in_h.with_columns(ppop=pl.col("in_h") / total)
            .sort(["in_h", "dst"], descending=[True, False])
            .head(200)
            .with_columns(pop_rank=pl.int_range(pl.len()) + 1)
            .rename({"dst": "item"})
        )
        self.max_ppop = float(self.pop["ppop"].max())

    def b0(self, q: pl.DataFrame, k: int = K) -> pl.DataFrame:
        return (
            q.select("q")
            .join(self.pop.select("item", "pop_rank").head(k + 1), how="cross")
            .filter(pl.col("item") != pl.col("q"))
            .pipe(topk, "q", ["pop_rank"], [False], k)
            .select("q", "item", "rank")
        )

    def b1(self, q: pl.DataFrame, min_h: int = 1, alpha: float = 0.0, k: int = K) -> pl.DataFrame:
        """score = (h + alpha * P_pop(C)) / (H(A) + alpha); denominator is constant per A,
        so ranking by h + alpha*P_pop(C). Non-edges score alpha*P_pop(C) < 1 <= any kept
        edge, which is exactly a popularity backfill."""
        e = (
            self.edges.join(q.select(src="q"), on="src")
            .filter(pl.col("h") >= min_h)
            .join(self.in_h, on="dst", how="left")
            .with_columns(score=pl.col("h") + alpha * pl.col("in_h") / self.in_h["in_h"].sum())
            .pipe(topk, "src", ["score", "dst"], [True, False], k)
            .select(q="src", item="dst", r="rank")
        )
        back = self.b0(q, k).select("q", "item", r=pl.col("rank") + 10_000)
        return (
            pl.concat([e, back])
            .group_by(["q", "item"])
            .agg(pl.col("r").min())
            .pipe(topk, "q", ["r"], [False], k)
            .select("q", "item", "rank")
        )

    def candidates(self, q: pl.DataFrame) -> pl.DataFrame:
        """Candidate generation + features, from history only."""
        qs = q.select(src="q")
        a_edges = (
            self.edges.join(qs, on="src")
            .join(self.out_h, on="src")
            .with_columns(p=pl.col("h") / pl.col("H"))
        )
        a_ranked = a_edges.sort(["src", "h", "dst"], descending=[False, True, False]).with_columns(
            b1_rank=pl.int_range(pl.len()).over("src") + 1
        )
        c_b1 = a_ranked.filter(pl.col("b1_rank") <= 50).select(q="src", item="dst", s=pl.lit(1))

        hop1 = topk(a_edges, "src", ["h", "dst"], [True, False], 20).select(
            q="src", b="dst", p1="p"
        )
        hop2 = (
            self.edges.join(hop1.select(src="b").unique(), on="src")
            .join(self.out_h, on="src")
            .with_columns(p2=pl.col("h") / pl.col("H"))
            .pipe(topk, "src", ["h", "dst"], [True, False], 20)
            .select(b="src", item="dst", p2="p2")
        )
        twohop = (
            hop1.join(hop2, on="b")
            .filter(pl.col("item") != pl.col("q"))
            .group_by(["q", "item"])
            .agg(twohop=(pl.col("p1") * pl.col("p2")).sum())
        )
        c_2h = topk(twohop, "q", ["twohop", "item"], [True, False], 50).select(
            "q", "item", s=pl.lit(2)
        )
        rev_all = self.edges.join(q.select(dst="q"), on="dst").select(
            q="dst", item="src", rev_h="h"
        )
        c_rev = topk(rev_all, "q", ["rev_h", "item"], [True, False], 20).select(
            "q", "item", s=pl.lit(3)
        )
        c_pop = self.b0(q, 20).select("q", "item", s=pl.lit(4))

        cand = (
            pl.concat([c_b1, c_2h, c_rev, c_pop])
            .group_by(["q", "item"])
            .agg(n_sources=pl.col("s").n_unique().cast(pl.Float64))
        )
        feats = (
            cand.join(
                a_ranked.select(q="src", item="dst", h_ac="h", p_c_given_a="p", b1_rank="b1_rank", pair_type="type"),
                on=["q", "item"],
                how="left",
            )
            .join(twohop, on=["q", "item"], how="left")
            .join(rev_all, on=["q", "item"], how="left")
            .join(self.in_h.select(item="dst", in_c="in_h"), on="item", how="left")
            .join(self.out_h.select(item="src", out_c="H"), on="item", how="left")
            .join(self.out_h.select(q="src", out_a="H"), on="q", how="left")
            .with_columns(
                pl.col(["h_ac", "p_c_given_a", "twohop", "rev_h", "in_c", "out_c", "out_a"])
                .fill_null(0)
                .cast(pl.Float64),
                pl.col("b1_rank").cast(pl.Float64),  # null -> NaN: not an out-edge
                pl.col("pair_type").cast(pl.Float64),
            )
            .sort(["q", "item"])
        )
        assert "t" not in feats.columns
        return feats


# --------------------------------------------------------------------------
# 5. Metrics
# --------------------------------------------------------------------------
def truth_tables(truth: pl.DataFrame, q: pl.DataFrame):
    tq = truth.join(q.select(src="q"), on="src").select(q="src", item="dst", t="t")
    tq = tq.with_columns(gain=pl.col("t").log1p())
    ideal = (
        topk(tq, "q", ["gain", "item"], [True, False], K)
        .with_columns(d=pl.col("gain") / (pl.col("rank") + 1).log(2))
        .group_by("q")
        .agg(idcg=pl.col("d").sum())
    )
    qstats = tq.group_by("q").agg(n_rel=pl.len(), t_sum=pl.col("t").sum()).join(ideal, on="q")
    return tq.select("q", "item", "t", "gain"), qstats


def per_query(recs: pl.DataFrame, tq: pl.DataFrame, qstats: pl.DataFrame, q: pl.DataFrame):
    hits = (
        recs.join(tq, on=["q", "item"], how="left")
        .with_columns(pl.col("gain").fill_null(0), pl.col("t").fill_null(0))
        .group_by("q")
        .agg(
            dcg=(pl.col("gain") / (pl.col("rank") + 1).log(2)).sum(),
            n_hit=(pl.col("t") > 0).sum(),
            t_hit=pl.col("t").sum(),
        )
    )
    return (
        q.select("q", "bucket")
        .join(qstats, on="q", how="left")
        .join(hits, on="q", how="left")
        .with_columns(pl.col(["dcg", "n_hit", "t_hit"]).fill_null(0))
        .select(
            "q",
            "bucket",
            ndcg=pl.col("dcg") / pl.col("idcg"),
            recall=pl.col("n_hit") / pl.col("n_rel"),
            recall_w=pl.col("t_hit") / pl.col("t_sum"),
            hit=(pl.col("n_hit") > 0).cast(pl.Float64),
        )
        .sort("q")
    )


METRICS = ["ndcg", "recall", "recall_w", "hit"]


def summarize(pq: pl.DataFrame, recs: pl.DataFrame, weights: dict, catalog: int) -> dict:
    out = {}
    by = pq.group_by("bucket").agg([pl.col(m).mean() for m in METRICS])
    rows = {r["bucket"]: r for r in by.iter_rows(named=True)}
    for b in BUCKETS:
        rb = rows[b]
        qb = pq.filter(pl.col("bucket") == b).select("q")
        cov = recs.join(qb, on="q")["item"].n_unique() / catalog
        out[b] = {m: float(rb[m]) for m in METRICS} | {"coverage": cov}
    out["overall"] = {m: float(sum(weights[b] * out[b][m] for b in BUCKETS)) for m in METRICS}
    out["overall"]["coverage"] = recs["item"].n_unique() / catalog
    return out


def bootstrap_delta(pa: pl.DataFrame, pb: pl.DataFrame, weights: dict) -> dict:
    """Stratified bootstrap of mean(A) - mean(B) per bucket and population-weighted overall."""
    rng = np.random.default_rng(SEED)
    j = pa.join(pb, on=["q", "bucket"], suffix="_b")
    res: dict = {}
    for m in METRICS:
        draws_a, draws_b = {}, {}
        for b in BUCKETS:
            jb = j.filter(pl.col("bucket") == b)
            a, bb = jb[m].to_numpy(), jb[f"{m}_b"].to_numpy()
            idx = rng.integers(0, len(a), size=(N_BOOT, len(a)))
            draws_a[b], draws_b[b] = a[idx].mean(1), bb[idx].mean(1)
            d = draws_a[b] - draws_b[b]
            res.setdefault(b, {})[m] = {
                "delta": float(a.mean() - bb.mean()),
                "lo": float(np.percentile(d, 2.5)),
                "hi": float(np.percentile(d, 97.5)),
                "rel": float((a.mean() - bb.mean()) / bb.mean()) if bb.mean() > 0 else None,
            }
        oa = sum(weights[b] * draws_a[b] for b in BUCKETS)
        ob = sum(weights[b] * draws_b[b] for b in BUCKETS)
        pt_a = sum(weights[b] * j.filter(pl.col("bucket") == b)[m].mean() for b in BUCKETS)
        pt_b = sum(weights[b] * j.filter(pl.col("bucket") == b)[f"{m}_b"].mean() for b in BUCKETS)
        rel = (oa - ob) / ob
        res.setdefault("overall", {})[m] = {
            "delta": float(pt_a - pt_b),
            "lo": float(np.percentile(oa - ob, 2.5)),
            "hi": float(np.percentile(oa - ob, 97.5)),
            "rel": float((pt_a - pt_b) / pt_b),
            "rel_lo": float(np.percentile(rel, 2.5)),
            "rel_hi": float(np.percentile(rel, 97.5)),
        }
    return res


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def rerank_recs(model, feats: pl.DataFrame, X: np.ndarray | None = None) -> pl.DataFrame:
    if X is None:
        X = feats.select(FEATURES).to_numpy()
    s = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else model.predict(X)
    return (
        feats.select("q", "item")
        .with_columns(score=pl.Series(s))
        .pipe(topk, "q", ["score", "item"], [True, False], K)
        .select("q", "item", "rank")
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "metrics.json"))
    ap.add_argument("--skip-perm", action="store_true")
    args = ap.parse_args()

    pairs, stats, titles = load_and_thin()
    hist = pairs.filter(pl.col("h") > 0).select("src", "dst", "type", "h")
    truth = pairs.filter(pl.col("t") > 0).select("src", "dst", "t")
    H = History(hist)
    log(f"history built; max P_pop={H.max_ppop:.2e} (so alpha*P_pop < 1 for alpha<=100)")
    assert 100 * H.max_ppop < 1
    catalog = stats["catalog_articles"]

    ev_q, fit_q, val_q = sample_queries(truth, H.out_h, stats)
    weights = stats["bucket_weights"]
    stats["eval_pct_of_sources"] = ev_q.height / stats["source_population_total"]

    # ---- B1 sweep on val
    tq_val, qs_val = truth_tables(truth, val_q)
    sweep = []
    for mh in MIN_H_GRID:
        for al in ALPHA_GRID:
            recs = H.b1(val_q, mh, al)
            s = summarize(per_query(recs, tq_val, qs_val, val_q), recs, weights, catalog)
            sweep.append({"min_h": mh, "alpha": al, **{k: s["overall"][k] for k in ["ndcg", "recall", "hit"]}})
    # Round before picking: alpha settings tie up to ~1e-16 float noise from parallel
    # group_by summation order; ties go to the simplest config (smallest min_h, alpha).
    sweep_df = (
        pl.DataFrame(sweep)
        .with_columns(ndcg_r=pl.col("ndcg").round(9))
        .sort(["ndcg_r", "min_h", "alpha"], descending=[True, False, False])
    )
    best = sweep_df.row(0, named=True)
    best_mh, best_al = best["min_h"], best["alpha"]
    log(f"B1 sweep (val):\n{pl.DataFrame(sweep)}\nbest min_h={best_mh} alpha={best_al}")

    # ---- Reranker training
    fit_feats = H.candidates(fit_q)
    assert "t" not in fit_feats.columns
    log(f"assert ok: features built from history only (columns: {sorted(fit_feats.columns)}); "
        "truth joined afterwards")
    tq_fit, qs_fit = truth_tables(truth, fit_q)
    fit = fit_feats.join(tq_fit.select("q", "item", "t"), on=["q", "item"], how="left").with_columns(
        y=(pl.col("t").fill_null(0) > 0).cast(pl.Int8)
    )
    stats["train_rows_full"] = fit.height
    stats["train_pos_rate"] = float(fit["y"].mean())
    cand_recall_fit = float(fit["t"].fill_null(0).sum() / qs_fit["t_sum"].sum())
    log(f"train candidates rows={fit.height:,} pos rate={stats['train_pos_rate']:.4f} "
        f"candidate click-recall={cand_recall_fit:.4f}")
    if fit.height > MAX_TRAIN_ROWS:
        rng = np.random.default_rng(SEED)
        keep = rng.random(fit.height) < MAX_TRAIN_ROWS / fit.height
        fit = fit.filter(pl.Series(keep))
        log(f"subsampled train rows uniformly to {fit.height:,}")
    stats["train_rows_used"] = fit.height
    model = HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.1,
        max_leaf_nodes=63,
        min_samples_leaf=100,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=20,
        random_state=SEED,
    )
    model.fit(fit.select(FEATURES).to_numpy(), fit["y"].to_numpy())
    stats["hgb_iters"] = int(model.n_iter_)
    log(f"HGB trained, iters={model.n_iter_}")
    model_g = HistGradientBoostingRegressor(
        max_iter=300,
        learning_rate=0.1,
        max_leaf_nodes=63,
        min_samples_leaf=100,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=20,
        random_state=SEED,
    )
    model_g.fit(fit.select(FEATURES).to_numpy(), fit["t"].fill_null(0).log1p().to_numpy())
    stats["hgb_graded_iters"] = int(model_g.n_iter_)
    log(f"HGB graded trained, iters={model_g.n_iter_}")
    del fit, fit_feats

    # ---- Eval
    tq_ev, qs_ev = truth_tables(truth, ev_q)
    recs = {
        "B0": H.b0(ev_q),
        "B1": H.b1(ev_q, best_mh, best_al),
        "B1_raw": H.b1(ev_q, 1, 0),
    }
    ev_feats = H.candidates(ev_q)
    stats["eval_candidate_rows"] = ev_feats.height
    cand_t = ev_feats.join(tq_ev, on=["q", "item"])
    cand_rec = (
        ev_q.join(qs_ev, on="q")
        .join(cand_t.group_by("q").agg(tc=pl.col("t").sum()), on="q", how="left")
        .with_columns(r=pl.col("tc").fill_null(0) / pl.col("t_sum"))
        .group_by("bucket")
        .agg(pl.col("r").mean())
    )
    stats["candidate_click_recall"] = {r["bucket"]: r["r"] for r in cand_rec.iter_rows(named=True)}
    log(f"eval candidate click-recall by bucket: {stats['candidate_click_recall']}")
    X_ev = ev_feats.select(FEATURES).to_numpy()
    recs["Reranker"] = rerank_recs(model, ev_feats, X_ev)
    recs["Reranker_graded"] = rerank_recs(model_g, ev_feats, X_ev)
    cold_ids = ev_q.filter(pl.col("bucket") == "cold").select("q")
    recs["Hybrid"] = pl.concat(
        [recs["B1"].join(cold_ids, on="q", how="anti"), recs["Reranker"].join(cold_ids, on="q")]
    ).sort(["q", "rank"])

    # Assert: B1 == B0 on cold eval queries.
    cold = ev_q.filter(pl.col("bucket") == "cold").select("q")
    c0 = recs["B0"].join(cold, on="q").sort(["q", "rank"])
    c1 = recs["B1"].join(cold, on="q").sort(["q", "rank"])
    assert c0.equals(c1), "B1 != B0 on cold queries"
    log(f"assert ok: B1 == B0 on {cold.height:,} cold eval queries")

    pqs = {m: per_query(r, tq_ev, qs_ev, ev_q) for m, r in recs.items()}
    results = {m: summarize(pqs[m], recs[m], weights, catalog) for m in recs}
    for m, s in results.items():
        log(f"{m}: " + json.dumps({b: {k: round(v, 4) for k, v in s[b].items()} for b in ["overall", *BUCKETS]}))
    boot = bootstrap_delta(pqs["Reranker"], pqs["B1"], weights)
    boot_g = bootstrap_delta(pqs["Reranker_graded"], pqs["B1"], weights)
    boot_h = bootstrap_delta(pqs["Hybrid"], pqs["B1"], weights)
    log("bootstrap Reranker_graded - B1 (nDCG@10): " + json.dumps(
        {b: {k: round(v, 4) for k, v in boot_g[b]["ndcg"].items() if v is not None} for b in ["overall", *BUCKETS]}))

    # Novel-pair slice: truth pairs that had h == 0 (never seen from A in history).
    seen = hist.join(ev_q.select(src="q"), on="src").select(q="src", item="dst")
    novel_truth = (
        truth.join(ev_q.select(src="q"), on="src")
        .select(q="src", item="dst", t="t")
        .join(seen, on=["q", "item"], how="anti")
        .select(src="q", dst="item", t="t")
    )
    tq_n, qs_n = truth_tables(novel_truth, ev_q)
    ev_q_n = ev_q.join(qs_n.select("q"), on="q")
    stats["novel_slice_queries"] = {
        r["bucket"]: r["len"] for r in ev_q_n.group_by("bucket").len().iter_rows(named=True)
    }
    stats["novel_slice_click_share"] = float(novel_truth["t"].sum() / qs_ev["t_sum"].sum())
    novel = {}
    for m, r in recs.items():
        pq = per_query(r, tq_n, qs_n, ev_q_n)
        novel[m] = {
            b: {k: float(v) for k, v in row.items() if k != "bucket"}
            for row in pq.group_by("bucket").agg([pl.col(x).mean() for x in METRICS]).iter_rows(named=True)
            for b in [row["bucket"]]
        }
        novel[m]["all_queries_unweighted"] = {x: float(pq[x].mean()) for x in METRICS}
    log(f"novel-pair slice queries {stats['novel_slice_queries']}, click share "
        f"{stats['novel_slice_click_share']:.4f}: " + json.dumps(
        {m: {b: round(v["ndcg"], 4) for b, v in d.items()} for m, d in novel.items()}))
    log("bootstrap Reranker - B1 (nDCG@10): " + json.dumps(
        {b: {k: round(v, 4) for k, v in boot[b]["ndcg"].items() if v is not None} for b in ["overall", *BUCKETS]}))

    # ---- Permutation importance on a sample of eval queries (query-level nDCG@10 drop)
    perm = {}
    if not args.skip_perm:
        rng = np.random.default_rng(SEED)
        sq = ev_q.sample(n=PERM_QUERIES, seed=SEED)
        sf = ev_feats.join(sq.select("q"), on="q")
        Xs = sf.select(FEATURES).to_numpy()
        tq_s, qs_s = truth_tables(truth, sq)

        def nd(X, mdl):
            r = rerank_recs(mdl, sf, X)
            return summarize(per_query(r, tq_s, qs_s, sq), r, weights, catalog)["overall"]["ndcg"]

        for name, mdl in [("Reranker", model), ("Reranker_graded", model_g)]:
            base = nd(Xs, mdl)
            pi = {}
            for i, f in enumerate(FEATURES):
                Xp = Xs.copy()
                Xp[:, i] = Xp[rng.permutation(len(Xp)), i]
                pi[f] = base - nd(Xp, mdl)
            perm[name] = {"base_ndcg": base} | dict(sorted(pi.items(), key=lambda kv: -kv[1]))
            log(f"permutation importance {name} (nDCG@10 drop, {PERM_QUERIES} eval queries, "
                f"base {base:.4f}): " + json.dumps({k: round(v, 4) for k, v in perm[name].items()}))

    # ---- Worked example: one torso source page, history vs truth
    n_tgt = pairs.group_by("src").len().filter(pl.col("len").is_between(6, 10))
    ex_q = (
        ev_q.filter(pl.col("bucket") == "torso")
        .join(n_tgt.select(q="src"), on="q")
        .join(titles.rename({"id": "q"}), on="q")
        .filter(~pl.col("title").str.contains('"'))
        .sort("q")
        .row(0, named=True)["q"]
    )
    ex = (
        pairs.filter(pl.col("src") == ex_q)
        .sort("n", descending=True)
        .join(titles.rename({"id": "dst", "title": "curr"}), on="dst")
        .sort("n", descending=True)
    )
    ex_title = titles.filter(pl.col("id") == ex_q)["title"][0]
    stats["worked_example"] = {
        "source": ex_title,
        "rows": ex.select("curr", "type", "n", "h", "t").to_dicts(),
        "source_n_targets": int(pairs.filter(pl.col("src") == ex_q).height),
    }
    log(f"worked example {ex_title}:\n{ex.select('curr', 'type', 'n', 'h', 't')}")

    out = {
        "stats": stats,
        "b1_sweep": sweep,
        "b1_best": {"min_h": best_mh, "alpha": best_al},
        "results": results,
        "bootstrap_reranker_minus_b1": boot,
        "bootstrap_reranker_graded_minus_b1": boot_g,
        "bootstrap_hybrid_minus_b1": boot_h,
        "novel_pair_slice": novel,
        "permutation_importance": perm,
        "runtime_s": time.time() - T0,
    }
    def rnd(x):
        if isinstance(x, float):
            return round(x, 10)
        if isinstance(x, dict):
            return {k: rnd(v) for k, v in x.items()}
        if isinstance(x, list):
            return [rnd(v) for v in x]
        return x

    out["runtime_s"] = round(out["runtime_s"], 1)
    Path(args.out).write_text(json.dumps(rnd(out), indent=2, default=str))
    log(f"wrote {args.out}")


if __name__ == "__main__":
    main()
