"""Build the labeled (A, C) pair tables for the Riot wiki reranker, on the
Wikipedia Clickstream proxy, with a temporal split.

    split   feature month (history)   label month (truth)
    train   2026-07                   2026-08
    test    2026-08                   2026-09

Each row is one (source page q, candidate page item) pair. Candidates come
from rules over the feature month only. The label is log1p(r), where r is
the label-month click count for the pair (0 when the pair is absent).

Outputs (git-ignored, under <sandbox>/data/wikipedia-clickstream/modeling/):
    months/<YYYY-MM>.parquet   filtered pairs per month (src, dst, type, n)
    titles.parquet             title <-> id over the three months
    queries_<split>.parquet    sampled source pages, bucket, seen flag
    pairs_<split>.parquet      candidate pairs + source flags + label
    truth_<split>.parquet      every label-month pair for the sampled queries

Run: uv run python3 modeling/build_dataset.py   (from the project folder)
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import polars as pl

SEED = 42
MONTHS = ["2026-07", "2026-08", "2026-09"]
SPLITS = {"train": ("2026-07", "2026-08"), "test": ("2026-08", "2026-09")}
N_QUERIES = {"train": 100_000, "test": 50_000}
MIN_PER_BUCKET = {"train": 10_000, "test": 5_000}
BUCKETS = ["cold", "tail", "torso", "head"]
EXCLUDED_PAGES = ["Main_Page"]
# Candidate generator caps (same rules as monkey-mode B1 + reranker sources).
CAP_OPENED_NEXT, CAP_TWOHOP, CAP_HOP, CAP_REVERSE, CAP_POP = 50, 50, 20, 20, 20

HERE = Path(__file__).resolve().parent
SANDBOX = HERE.parents[2]
RAW = SANDBOX / "data" / "wikipedia-clickstream"
OUT = RAW / "modeling"
T0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


def topk(df: pl.DataFrame, group: str, by: list[str], desc: list[bool], k: int) -> pl.DataFrame:
    return (
        df.sort([group, *by], descending=[False, *desc])
        .with_columns(rank=pl.int_range(pl.len()).over(group) + 1)
        .filter(pl.col("rank") <= k)
    )


def bucket_expr(col: str) -> pl.Expr:
    c = pl.col(col)
    return (
        pl.when(c == 0).then(pl.lit("cold"))
        .when(c <= 50).then(pl.lit("tail"))
        .when(c <= 1000).then(pl.lit("torso"))
        .otherwise(pl.lit("head"))
    )


# ---------------------------------------------------------------------------
# 1. Load and filter each month; one id space over all months
# ---------------------------------------------------------------------------
def load_months() -> tuple[dict[str, pl.DataFrame], dict]:
    stats: dict = {"months": {}}
    raw = {}
    for m in MONTHS:
        df = pl.read_csv(
            RAW / f"clickstream-enwiki-{m}.tsv.gz",
            separator="\t",
            has_header=False,
            quote_char=None,
            schema={"prev": pl.String, "curr": pl.String, "type": pl.String, "n": pl.Int64},
        )
        s = {"raw_rows": df.height, "raw_clicks": int(df["n"].sum())}
        df = df.filter(
            pl.col("type").is_in(["link", "other"])
            & (pl.col("prev") != pl.col("curr"))
            & ~pl.col("prev").is_in(EXCLUDED_PAGES)
            & ~pl.col("curr").is_in(EXCLUDED_PAGES)
        )
        s |= {"rows": df.height, "clicks": int(df["n"].sum()), "min_n": int(df["n"].min())}
        stats["months"][m] = s
        log(f"{m}: raw {s['raw_rows']:,} -> filtered {s['rows']:,} rows, min n = {s['min_n']}")
        raw[m] = df

    titles = (
        pl.concat([d.select(title=c) for d in raw.values() for c in ("prev", "curr")])
        .unique()
        .sort("title")
        .with_row_index("id")
        .with_columns(pl.col("id").cast(pl.Int32))
    )
    stats["catalog_pages"] = titles.height
    months = {}
    for m, df in raw.items():
        months[m] = (
            df.join(titles.rename({"title": "prev", "id": "src"}), on="prev")
            .join(titles.rename({"title": "curr", "id": "dst"}), on="curr")
            .select("src", "dst", type=(pl.col("type") == "other").cast(pl.Int8), n="n")
            .sort(["src", "dst"])
        )
        assert months[m].height == df.height, "title join dropped rows"
    (OUT / "months").mkdir(parents=True, exist_ok=True)
    titles.write_parquet(OUT / "titles.parquet")
    for m, df in months.items():
        df.write_parquet(OUT / "months" / f"{m}.parquet")
    log(f"catalog = {titles.height:,} pages over {len(MONTHS)} months")
    return months, stats


# ---------------------------------------------------------------------------
# 2. Queries: sources with label-month traffic, bucketed by feature month
# ---------------------------------------------------------------------------
def sample_queries(split: str, feat: pl.DataFrame, lab: pl.DataFrame, stats: dict) -> pl.DataFrame:
    out_f = feat.group_by("src").agg(src_out_f=pl.col("n").sum())
    seen_f = pl.concat([feat.select(q="src"), feat.select(q="dst")]).unique()
    src = (
        lab.select(q="src").unique()
        .join(out_f.rename({"src": "q"}), on="q", how="left")
        .with_columns(pl.col("src_out_f").fill_null(0))
        .join(seen_f.with_columns(seen_f=pl.lit(True)), on="q", how="left")
        .with_columns(pl.col("seen_f").fill_null(False), bucket=bucket_expr("src_out_f"))
        .sort("q")
    )
    pop = {r["bucket"]: r["len"] for r in src.group_by("bucket").len().iter_rows(named=True)}
    total = sum(pop.values())
    rng = np.random.default_rng([SEED, list(SPLITS).index(split)])
    parts = []
    for b in BUCKETS:
        part = src.filter(pl.col("bucket") == b)
        n = min(max(MIN_PER_BUCKET[split], round(N_QUERIES[split] * pop.get(b, 0) / total)), part.height)
        parts.append(part[rng.choice(part.height, n, replace=False).tolist()])
    q = pl.concat(parts).sort("q")
    stats["population"] = {b: pop.get(b, 0) for b in BUCKETS}
    stats["population_total"] = total
    stats["queries"] = {r["bucket"]: r["len"] for r in q.group_by("bucket").len().iter_rows(named=True)}
    stats["queries_total"] = q.height
    stats["queries_share_of_population"] = q.height / total
    stats["cold_never_seen"] = int(q.filter((pl.col("bucket") == "cold") & ~pl.col("seen_f")).height)
    log(f"{split}: {q.height:,} queries ({q.height / total:.2%} of {total:,}) {stats['queries']}")
    return q


# ---------------------------------------------------------------------------
# 3. Candidates from the feature month only
# ---------------------------------------------------------------------------
def candidates(q: pl.DataFrame, feat: pl.DataFrame) -> pl.DataFrame:
    qs = q.select(src="q")
    out_f = feat.group_by("src").agg(H=pl.col("n").sum())
    a_edges = feat.join(qs, on="src").join(out_f, on="src").with_columns(p=pl.col("n") / pl.col("H"))

    c_next = topk(a_edges, "src", ["n", "dst"], [True, False], CAP_OPENED_NEXT).select(
        q="src", item="dst", src_flag=pl.lit("opened_next")
    )
    hop1 = topk(a_edges, "src", ["n", "dst"], [True, False], CAP_HOP).select(q="src", b="dst", p1="p")
    hop2 = (
        feat.join(hop1.select(src="b").unique(), on="src")
        .join(out_f, on="src")
        .with_columns(p2=pl.col("n") / pl.col("H"))
        .pipe(topk, "src", ["n", "dst"], [True, False], CAP_HOP)
        .select(b="src", item="dst", p2="p2")
    )
    twohop = (
        hop1.join(hop2, on="b")
        .group_by(["q", "item"])
        .agg(s=(pl.col("p1") * pl.col("p2")).sum())
    )
    c_2hop = topk(twohop, "q", ["s", "item"], [True, False], CAP_TWOHOP).select(
        "q", "item", src_flag=pl.lit("twohop")
    )
    rev = feat.join(q.select(dst="q"), on="dst").select(q="dst", item="src", n="n")
    c_rev = topk(rev, "q", ["n", "item"], [True, False], CAP_REVERSE).select(
        "q", "item", src_flag=pl.lit("reverse")
    )
    pop = (
        feat.group_by("dst").agg(in_n=pl.col("n").sum())
        .sort(["in_n", "dst"], descending=[True, False])
        .head(CAP_POP + 1)
        .select(item="dst", pop_rank=pl.int_range(pl.len()))
    )
    c_pop = (
        qs.select(q="src").join(pop, how="cross")
        .filter(pl.col("item") != pl.col("q"))
        .pipe(topk, "q", ["pop_rank"], [False], CAP_POP)
        .select("q", "item", src_flag=pl.lit("popular"))
    )

    cand = (
        pl.concat([c_next, c_2hop, c_rev, c_pop])
        .filter(pl.col("item") != pl.col("q"))
        .with_columns(v=pl.lit(True))
        .pivot(on="src_flag", index=["q", "item"], values="v", aggregate_function="first")
    )
    flags = ["opened_next", "twohop", "reverse", "popular"]
    cand = cand.with_columns([pl.col(f).fill_null(False).alias(f"cand_{f}") for f in flags]).drop(flags)
    return cand.sort(["q", "item"])


# ---------------------------------------------------------------------------
# 4. Labels and truth
# ---------------------------------------------------------------------------
def build_split(split: str, months: dict, stats: dict) -> None:
    fm, lm = SPLITS[split]
    feat, lab = months[fm], months[lm]
    s: dict = {"feature_month": fm, "label_month": lm}
    q = sample_queries(split, feat, lab, s)

    truth = lab.join(q.select(src="q"), on="src").select(q="src", item="dst", r="n")
    cand = candidates(q, feat)
    pairs = (
        cand.join(truth, on=["q", "item"], how="left")
        .with_columns(pl.col("r").fill_null(0))
        .with_columns(label=pl.col("r").cast(pl.Float64).log1p())
        .join(q.select("q", "bucket"), on="q")
    )
    assert pairs.select(pl.col("q") == pl.col("item")).to_series().sum() == 0
    assert pairs.unique(["q", "item"]).height == pairs.height, "duplicate pairs"

    pos_rate = float((pairs["r"] > 0).mean())
    assert 0.005 < pos_rate < 0.95, f"degenerate positive rate {pos_rate:.4f}"

    # Candidate recall over all truth pages (diagnostic; the ranker can't do better).
    by_b = (
        truth.join(q.select("q", "bucket"), on="q")
        .join(cand.select("q", "item", found=pl.lit(True)), on=["q", "item"], how="left")
        .with_columns(pl.col("found").fill_null(False))
        .group_by("bucket")
        .agg(
            recall=pl.col("found").mean(),
            recall_w=(pl.col("found") * pl.col("r")).sum() / pl.col("r").sum(),
        )
    )
    s["candidate_recall"] = {
        r["bucket"]: {"recall": round(r["recall"], 4), "recall_w": round(r["recall_w"], 4)}
        for r in by_b.iter_rows(named=True)
    }
    s["pairs"] = pairs.height
    s["truth_pairs"] = truth.height
    s["positive_rate"] = round(pos_rate, 4)
    s["candidates_per_query_mean"] = round(pairs.height / q.height, 1)
    log(
        f"{split}: {pairs.height:,} pairs, {s['candidates_per_query_mean']} per query, "
        f"positive rate {pos_rate:.3f}, candidate recall {s['candidate_recall']}"
    )
    q.write_parquet(OUT / f"queries_{split}.parquet")
    pairs.write_parquet(OUT / f"pairs_{split}.parquet")
    truth.write_parquet(OUT / f"truth_{split}.parquet")
    stats[split] = s


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    months, stats = load_months()
    for split in SPLITS:
        build_split(split, months, stats)
    tq = pl.read_parquet(OUT / "queries_train.parquet").select("q")
    eq = pl.read_parquet(OUT / "queries_test.parquet").select("q")
    stats["query_overlap_train_test"] = tq.join(eq, on="q").height
    (HERE / "build_dataset_stats.json").write_text(json.dumps(stats, indent=2))
    log(f"done; train/test query overlap = {stats['query_overlap_train_test']:,}")


if __name__ == "__main__":
    main()
