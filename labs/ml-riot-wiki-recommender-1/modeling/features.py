"""Pair features for the Riot wiki reranker, on the Wikipedia proxy.

transform(pairs, split) adds feature columns to a pair table from
build_dataset.py. Every feature uses only the split's feature month (the
history before cutoff T). Nothing is fit on labels, so the same function
serves train and test with no leak: train uses July history, test uses
August history.

Run (writes the train output table):
    uv run python3 modeling/features.py          (from the project folder)
"""

from __future__ import annotations

import json
import time
from datetime import date
from functools import lru_cache
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[2] / "data" / "wikipedia-clickstream" / "modeling"
SPLITS = {"train": ("2026-07", "2026-08-01"), "test": ("2026-08", "2026-09-01")}
WINDOW_DAYS = 31  # feature window = one calendar month
CAP_HOP = 20      # same per-hop cap as the two-hop candidate rule

FEATURES = [
    # opened-next A -> C (the V0 baseline signal)
    "log_n_ac", "p_c_given_a", "rank_ac", "is_link_ac",
    # reverse C -> A (back-link traffic)
    "log_n_ca", "p_a_given_c",
    # two-hop A -> B -> C
    "twohop", "twohop_paths",
    # candidate page C
    "log_in_c", "log_out_c", "log_views_c", "log_in_c_per_day", "item_age_days", "item_is_new",
    # source page A
    "log_out_a", "log_views_a", "q_age_days", "q_is_new",
    # which rules proposed C
    "cand_opened_next", "cand_twohop", "cand_reverse", "cand_popular", "n_sources",
]


@lru_cache(maxsize=2)
def page_age(split: str) -> pl.DataFrame:
    """Age in days at cutoff T, from page ids calibrated to dates.
    Riot: replace with T - wiki.pages.created."""
    t = date.fromisoformat(SPLITS[split][1])
    cal = json.loads((HERE / "page_id_dates.json").read_text())
    ids = np.array(list(cal.values()), dtype=float)
    days = np.array([(t - date.fromisoformat(d)).days for d in cal], dtype=float)
    pages = pl.read_parquet(OUT / f"pages_{split}.parquet", columns=["page", "page_id", "views", "is_new"])
    pid = pages["page_id"].cast(pl.Float64).to_numpy()
    # Linear between calibration points; pages older than the first point get
    # at least that age (only "older than ~4 months" matters here).
    age = np.interp(pid, ids, days, left=np.nan, right=0.0)
    age = np.where(np.isnan(pid), np.nan, np.where(pid < ids[0], np.maximum(days[0], 365.0), age))
    # NaN -> null: a page with no enwiki page id (renamed or deleted) has unknown age.
    return pages.with_columns(age_days=pl.Series(np.clip(age, 0, None)).fill_nan(None))


@lru_cache(maxsize=2)
def history(split: str) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """The feature month and its per-page totals, loaded once per process.
    Serving calls transform() many times; the history doesn't change."""
    feat = pl.read_parquet(OUT / "months" / f"{SPLITS[split][0]}.parquet")
    out_n = feat.group_by("src").agg(out_n=pl.col("n").sum())
    in_n = feat.group_by("dst").agg(in_n=pl.col("n").sum())
    return feat, out_n, in_n


def transform(pairs: pl.DataFrame, split: str) -> pl.DataFrame:
    feat, out_n, in_n = history(split)
    ages = page_age(split)
    qs = pairs.select("q").unique()

    # A -> C edges of the queries, with rank among A's out-edges.
    a_edges = (
        feat.join(qs.rename({"q": "src"}), on="src")
        .join(out_n, on="src")
        .sort(["src", "n", "dst"], descending=[False, True, False])
        .with_columns(rank_ac=pl.int_range(pl.len()).over("src") + 1, p=pl.col("n") / pl.col("out_n"))
    )
    ac = a_edges.select(
        q="src", item="dst", n_ac="n", p_c_given_a="p", rank_ac="rank_ac",
        is_link_ac=(pl.col("type") == 0).cast(pl.Float64),
    )
    # C -> A edges.
    ca = (
        feat.join(qs.rename({"q": "dst"}), on="dst")
        .join(out_n, on="src")
        .select(q="dst", item="src", n_ca="n", p_a_given_c=pl.col("n") / pl.col("out_n"))
    )
    # Two-hop score and path count (each hop capped at CAP_HOP).
    hop1 = a_edges.filter(pl.col("rank_ac") <= CAP_HOP).select(q="src", b="dst", p1="p")
    hop2 = (
        feat.join(hop1.select(src="b").unique(), on="src")
        .join(out_n, on="src")
        .sort(["src", "n", "dst"], descending=[False, True, False])
        .filter(pl.int_range(pl.len()).over("src") < CAP_HOP)
        .select(b="src", item="dst", p2=pl.col("n") / pl.col("out_n"))
    )
    two = (
        hop1.join(hop2, on="b")
        .join(pairs.select("q", "item"), on=["q", "item"], how="semi")
        .group_by(["q", "item"])
        .agg(twohop=(pl.col("p1") * pl.col("p2")).sum(), twohop_paths=pl.len().cast(pl.Float64))
    )

    item_pages = (
        ages.join(in_n.rename({"dst": "page"}), on="page", how="left")
        .join(out_n.rename({"src": "page"}), on="page", how="left")
        .with_columns(pl.col("in_n", "out_n").fill_null(0))
        .select(
            item="page",
            log_in_c=pl.col("in_n").log1p(),
            log_out_c=pl.col("out_n").log1p(),
            log_views_c=pl.col("views").log1p(),
            # Counts per day the page existed in the window: a 3-day-old page
            # with 20 clicks is hot, not long-tail.
            log_in_c_per_day=(
                pl.col("in_n") / pl.col("age_days").fill_null(WINDOW_DAYS).clip(1, WINDOW_DAYS)
            ).log1p(),
            item_age_days=pl.col("age_days"),
            item_is_new=pl.col("is_new").cast(pl.Float64),
        )
    )
    q_pages = item_pages.select(
        q="item", log_out_a="log_out_c", log_views_a="log_views_c",
        q_age_days="item_age_days", q_is_new="item_is_new",
    )

    flags = ["cand_opened_next", "cand_twohop", "cand_reverse", "cand_popular"]
    df = (
        pairs.join(ac, on=["q", "item"], how="left")
        .join(ca, on=["q", "item"], how="left")
        .join(two, on=["q", "item"], how="left")
        .join(item_pages, on="item", how="left")
        .join(q_pages, on="q", how="left")
        .with_columns(
            pl.col("p_c_given_a", "p_a_given_c", "twohop", "twohop_paths").fill_null(0),
            # rank_ac and is_link_ac stay null (NaN) when there is no A -> C edge.
            pl.col("rank_ac").cast(pl.Float64),
            pl.col(flags).cast(pl.Float64),
            log_n_ac=pl.col("n_ac").fill_null(0).log1p(),
            log_n_ca=pl.col("n_ca").fill_null(0).log1p(),
            n_sources=pl.sum_horizontal(pl.col(flags).cast(pl.Float64)),
        )
        .drop("n_ac", "n_ca")
    )
    assert df.height == pairs.height, "feature joins changed the row count"
    return df


def main() -> None:
    t0 = time.time()
    pairs = pl.read_parquet(OUT / "pairs_train.parquet")
    df = transform(pairs, "train")
    keep = ["q", "item", "q_slice", "item_slice", "r", "label", *FEATURES]
    df.select(keep).write_parquet(OUT / "features_train.parquet")
    print(f"features_train: {df.height:,} rows x {len(FEATURES)} features in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
