"""Build the labeled (A, C) pair tables for the Riot wiki reranker, on the
Wikipedia Clickstream proxy, with a temporal split.

    split   feature month (history)   label month (truth)   cutoff T
    train   2026-07                   2026-08               2026-08-01
    test    2026-08                   2026-09               2026-09-01

Each row is one (source page q, candidate page item) pair. Candidates come
from rules over the feature month only. The label is log1p(r), where r is
the label-month click count for the pair (0 when the pair is absent).

Slices (PRD, Metrics - offline), at each cutoff T, for every page:
    age axis      new: created < 14 days before T, or after T
                  (page id >= the calibrated id for T - 14 days)
    traffic axis  established pages only, feature month:
                  dormant    0 views (no row with the page as target)
                  long-tail  activity up to p50 of pages with activity > 0
                             (pages with views but 0 activity go here)
                  torso      p50 - p90
                  head       above p90
    activity      query side: out-clicks to wiki pages (q_slice)
                  item side:  in-clicks from wiki pages (item_slice)

Outputs (git-ignored, under <sandbox>/data/wikipedia-clickstream/modeling/):
    months/<YYYY-MM>.parquet        filtered pairs (src, dst, type, n)
    months/views_<YYYY-MM>.parquet  views per page, all referrers
    titles.parquet                  title <-> id, plus enwiki page_id
    pages_<split>.parquet           every page: age, activity, slices
    queries_<split>.parquet         sampled source pages and slice
    pairs_<split>.parquet           candidate pairs + flags + label + slices
    truth_<split>.parquet           every label-month pair for the queries

Inputs from modeling/calibrate_page_age.py: page_ids.parquet (data dir) and
modeling/page_id_dates.json.

Run: uv run python3 modeling/build_dataset.py   (from the project folder)
"""

from __future__ import annotations

import json
import time
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl

SEED = 42
MONTHS = ["2026-07", "2026-08", "2026-09"]
SPLITS = {"train": ("2026-07", "2026-08"), "test": ("2026-08", "2026-09")}
CUTOFF = {"train": "2026-08-01", "test": "2026-09-01"}
NEW_DAYS = 14
N_QUERIES = {"train": 100_000, "test": 50_000}
MIN_PER_SLICE = {"train": 10_000, "test": 5_000}
SLICES = ["new", "dormant", "long_tail", "torso", "head"]
EXCLUDED_PAGES = ["Main_Page"]
# Candidate generator caps (same rules as monkey-mode B1 + reranker sources).
CAP_OPENED_NEXT, CAP_TWOHOP, CAP_HOP, CAP_REVERSE, CAP_POP = 50, 50, 20, 20, 20

HERE = Path(__file__).resolve().parent
SANDBOX = HERE.parents[2]
RAW = SANDBOX / "data" / "wikipedia-clickstream"
OUT = RAW / "modeling"
PAGE_IDS = RAW / "pages" / "page_ids.parquet"
ID_DATES = HERE / "page_id_dates.json"
T0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


def topk(df: pl.DataFrame, group: str, by: list[str], desc: list[bool], k: int) -> pl.DataFrame:
    return (
        df.sort([group, *by], descending=[False, *desc])
        .with_columns(rank=pl.int_range(pl.len()).over(group) + 1)
        .filter(pl.col("rank") <= k)
    )


# ---------------------------------------------------------------------------
# 1. Load and filter each month; one id space over all months
# ---------------------------------------------------------------------------
def load_months() -> tuple[dict[str, pl.DataFrame], dict[str, pl.DataFrame], pl.DataFrame, dict]:
    stats: dict = {"months": {}}
    raw, views_raw = {}, {}
    for m in MONTHS:
        df = pl.read_csv(
            RAW / f"clickstream-enwiki-{m}.tsv.gz",
            separator="\t",
            has_header=False,
            quote_char=None,
            schema={"prev": pl.String, "curr": pl.String, "type": pl.String, "n": pl.Int64},
        )
        s = {"raw_rows": df.height, "raw_clicks": int(df["n"].sum())}
        # Views: every referrer (search, external, empty, other pages).
        views_raw[m] = df.group_by("curr").agg(views=pl.col("n").sum())
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

    page_ids = pl.read_parquet(PAGE_IDS).unique("title", keep="first")
    titles = (
        pl.concat([d.select(title=c) for d in raw.values() for c in ("prev", "curr")])
        .unique()
        .sort("title")
        .with_row_index("id")
        .with_columns(pl.col("id").cast(pl.Int32))
        .join(page_ids, on="title", how="left")
    )
    stats["catalog_pages"] = titles.height
    stats["catalog_without_page_id"] = int(titles["page_id"].null_count())
    months, views = {}, {}
    for m, df in raw.items():
        months[m] = (
            df.join(titles.select(prev="title", src="id"), on="prev")
            .join(titles.select(curr="title", dst="id"), on="curr")
            .select("src", "dst", type=(pl.col("type") == "other").cast(pl.Int8), n="n")
            .sort(["src", "dst"])
        )
        assert months[m].height == df.height, "title join dropped rows"
        views[m] = views_raw[m].join(titles.select(curr="title", page="id"), on="curr").select("page", "views")
    (OUT / "months").mkdir(parents=True, exist_ok=True)
    titles.write_parquet(OUT / "titles.parquet")
    for m in MONTHS:
        months[m].write_parquet(OUT / "months" / f"{m}.parquet")
        views[m].write_parquet(OUT / "months" / f"views_{m}.parquet")
    log(
        f"catalog = {titles.height:,} pages over {len(MONTHS)} months; "
        f"{stats['catalog_without_page_id']:,} without an enwiki page id (renamed or deleted)"
    )
    return months, views, titles, stats


# ---------------------------------------------------------------------------
# 2. Page profile at cutoff T: age and traffic slices, both sides
# ---------------------------------------------------------------------------
def page_profile(split: str, feat: pl.DataFrame, views: pl.DataFrame, titles: pl.DataFrame, s: dict) -> pl.DataFrame:
    id_dates = json.loads(ID_DATES.read_text())
    t = date.fromisoformat(CUTOFF[split])
    new_from = id_dates[(t - timedelta(days=NEW_DAYS)).isoformat()]
    born_from = id_dates[t.isoformat()]
    pages = (
        titles.select(page="id", page_id="page_id")
        .join(views, on="page", how="left")
        .join(feat.group_by("src").agg(out_f=pl.col("n").sum()).rename({"src": "page"}), on="page", how="left")
        .join(feat.group_by("dst").agg(in_f=pl.col("n").sum()).rename({"dst": "page"}), on="page", how="left")
        .with_columns(pl.col("views", "out_f", "in_f").fill_null(0))
        .with_columns(
            age=pl.when(pl.col("page_id").is_null()).then(pl.lit("unknown"))
            .when(pl.col("page_id") >= born_from).then(pl.lit("born_after_T"))
            .when(pl.col("page_id") >= new_from).then(pl.lit("new_lt14d"))
            .otherwise(pl.lit("established"))
        )
        .with_columns(is_new=pl.col("age").is_in(["born_after_T", "new_lt14d"]))
    )
    est = pages.filter(~pl.col("is_new") & (pl.col("views") > 0))
    thr = {}
    for side, col in (("query", "out_f"), ("item", "in_f")):
        act = est.filter(pl.col(col) > 0)[col]
        thr[side] = {"p50": float(act.quantile(0.5)), "p90": float(act.quantile(0.9))}

    def slice_expr(col: str, side: str) -> pl.Expr:
        return (
            pl.when(pl.col("is_new")).then(pl.lit("new"))
            .when(pl.col("views") == 0).then(pl.lit("dormant"))
            .when(pl.col(col) <= thr[side]["p50"]).then(pl.lit("long_tail"))
            .when(pl.col(col) <= thr[side]["p90"]).then(pl.lit("torso"))
            .otherwise(pl.lit("head"))
        )

    pages = pages.with_columns(q_slice=slice_expr("out_f", "query"), item_slice=slice_expr("in_f", "item"))
    s["new_page_id_from"] = new_from
    s["born_after_T_page_id_from"] = born_from
    s["traffic_thresholds"] = thr
    s["catalog_by_age"] = {r["age"]: r["len"] for r in pages.group_by("age").len().iter_rows(named=True)}
    s["catalog_by_item_slice"] = {
        r["item_slice"]: r["len"] for r in pages.group_by("item_slice").len().iter_rows(named=True)
    }
    log(f"{split}: thresholds {thr}; catalog by age {s['catalog_by_age']}")
    pages.write_parquet(OUT / f"pages_{split}.parquet")
    return pages


# ---------------------------------------------------------------------------
# 3. Queries: sources with label-month traffic, stratified by q_slice
# ---------------------------------------------------------------------------
def sample_queries(split: str, lab: pl.DataFrame, pages: pl.DataFrame, s: dict) -> pl.DataFrame:
    src = (
        lab.select(q="src").unique()
        .join(pages.select(q="page", src_out_f="out_f", views_f="views", age="age", q_slice="q_slice"), on="q")
        .sort("q")
    )
    pop = {r["q_slice"]: r["len"] for r in src.group_by("q_slice").len().iter_rows(named=True)}
    total = sum(pop.values())
    rng = np.random.default_rng([SEED, list(SPLITS).index(split)])
    parts = []
    for b in SLICES:
        part = src.filter(pl.col("q_slice") == b)
        n = min(max(MIN_PER_SLICE[split], round(N_QUERIES[split] * pop.get(b, 0) / total)), part.height)
        parts.append(part[rng.choice(part.height, n, replace=False).tolist()])
    q = pl.concat(parts).sort("q")
    s["population"] = {b: pop.get(b, 0) for b in SLICES}
    s["population_total"] = total
    s["queries"] = {b: q.filter(pl.col("q_slice") == b).height for b in SLICES}
    s["queries_total"] = q.height
    s["queries_share_of_population"] = q.height / total
    s["queries_new_by_age"] = {
        r["age"]: r["len"] for r in q.filter(pl.col("q_slice") == "new").group_by("age").len().iter_rows(named=True)
    }
    log(f"{split}: {q.height:,} queries ({q.height / total:.2%} of {total:,}) {s['queries']}")
    return q


# ---------------------------------------------------------------------------
# 4. Candidates from the feature month only
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
# 5. Labels and truth
# ---------------------------------------------------------------------------
def recall_by(truth: pl.DataFrame, cand: pl.DataFrame, by: str) -> dict:
    """Candidate recall over all truth pages (the ranker can't do better)."""
    t = (
        truth.join(cand.select("q", "item", found=pl.lit(True)), on=["q", "item"], how="left")
        .with_columns(pl.col("found").fill_null(False))
        .group_by(by)
        .agg(
            truth_pairs=pl.len(),
            recall=pl.col("found").mean(),
            recall_w=(pl.col("found") * pl.col("r")).sum() / pl.col("r").sum(),
        )
    )
    return {
        r[by]: {"truth_pairs": r["truth_pairs"], "recall": round(r["recall"], 4), "recall_w": round(r["recall_w"], 4)}
        for r in t.iter_rows(named=True)
    }


def build_split(split: str, months: dict, views: dict, titles: pl.DataFrame, stats: dict) -> None:
    fm, lm = SPLITS[split]
    feat, lab = months[fm], months[lm]
    s: dict = {"feature_month": fm, "label_month": lm, "cutoff": CUTOFF[split]}
    pages = page_profile(split, feat, views[fm], titles, s)
    q = sample_queries(split, lab, pages, s)
    item_slice = pages.select(item="page", item_slice="item_slice")

    truth = (
        lab.join(q.select(src="q"), on="src")
        .select(q="src", item="dst", r="n")
        .join(q.select("q", "q_slice"), on="q")
        .join(item_slice, on="item")
    )
    cand = candidates(q, feat)
    pairs = (
        cand.join(truth.select("q", "item", "r"), on=["q", "item"], how="left")
        .with_columns(pl.col("r").fill_null(0))
        .with_columns(label=pl.col("r").cast(pl.Float64).log1p())
        .join(q.select("q", "q_slice"), on="q")
        .join(item_slice, on="item")
    )
    assert pairs.select(pl.col("q") == pl.col("item")).to_series().sum() == 0
    assert pairs.unique(["q", "item"]).height == pairs.height, "duplicate pairs"
    assert pairs.height == cand.height, "slice join dropped pairs"

    pos_rate = float((pairs["r"] > 0).mean())
    assert 0.005 < pos_rate < 0.95, f"degenerate positive rate {pos_rate:.4f}"

    s["candidate_recall_query_side"] = recall_by(truth, cand, "q_slice")
    s["candidate_recall_item_side"] = recall_by(truth, cand, "item_slice")
    s["pairs"] = pairs.height
    s["truth_pairs"] = truth.height
    s["positive_rate"] = round(pos_rate, 4)
    s["candidates_per_query_mean"] = round(pairs.height / q.height, 1)
    log(f"{split}: {pairs.height:,} pairs, {s['candidates_per_query_mean']} per query, positive rate {pos_rate:.3f}")
    log(f"{split}: candidate recall, query side {s['candidate_recall_query_side']}")
    log(f"{split}: candidate recall, item side {s['candidate_recall_item_side']}")
    q.write_parquet(OUT / f"queries_{split}.parquet")
    pairs.write_parquet(OUT / f"pairs_{split}.parquet")
    truth.write_parquet(OUT / f"truth_{split}.parquet")
    stats[split] = s


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    months, views, titles, stats = load_months()
    for split in SPLITS:
        build_split(split, months, views, titles, stats)
    tq = pl.read_parquet(OUT / "queries_train.parquet").select("q")
    eq = pl.read_parquet(OUT / "queries_test.parquet").select("q")
    stats["query_overlap_train_test"] = tq.join(eq, on="q").height
    (HERE / "build_dataset_stats.json").write_text(json.dumps(stats, indent=2))
    log(f"done; train/test query overlap = {stats['query_overlap_train_test']:,}")


if __name__ == "__main__":
    main()
