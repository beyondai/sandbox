"""Profile the train pair table (never the test rows) and write
modeling/01-data.json. Run after build_dataset.py.

Run: uv run python3 modeling/profile_data.py   (from the project folder)
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[2] / "data" / "wikipedia-clickstream" / "modeling"
REL = "../../../data/wikipedia-clickstream/modeling"  # from modeling/


def num_profile(s: pl.Series) -> dict:
    s = s.cast(pl.Float64)
    return {
        "min": round(s.min(), 4), "max": round(s.max(), 4), "mean": round(s.mean(), 4),
        "median": round(s.median(), 4), "std": round(s.std(), 4), "skew": round(s.skew(), 4),
    }


def main() -> None:
    stats = json.loads((HERE / "build_dataset_stats.json").read_text())
    pairs = pl.read_parquet(OUT / "pairs_train.parquet")
    q = pl.read_parquet(OUT / "queries_train.parquet")
    df = pairs.join(q.select("q", "src_out_f", "seen_f"), on="q")
    per_q = df.group_by("q").agg(
        n_cand=pl.len(), n_pos=(pl.col("r") > 0).sum(), bucket=pl.col("bucket").first()
    )

    pos_by_bucket = {
        r["bucket"]: round(r["pos"], 4)
        for r in df.group_by("bucket").agg(pos=(pl.col("r") > 0).mean()).iter_rows(named=True)
    }
    no_pos = per_q.group_by("bucket").agg(share=(pl.col("n_pos") == 0).mean())
    flags = [c for c in df.columns if c.startswith("cand_")]
    flag_rates = {f: round(float(df[f].mean()), 4) for f in flags}
    flag_pos = {
        f: round(float(df.filter(pl.col(f))["r"].gt(0).mean()), 4) for f in flags
    }

    quality = [
        "proxy: monthly click counts, not distinct readers in 14 days",
        "proxy: pairs with fewer than 10 clicks a month are removed upstream, so "
        "label 0 means r < 10, not r = 0",
        "proxy: no session ids, no page text, no permissions or archive status",
        "duplicate (q, item) pairs: 0 (asserted in build_dataset.py)",
        "self pairs (q = item): 0 (asserted)",
        f"label is zero-inflated: {1 - stats['train']['positive_rate']:.1%} of pairs "
        "have label 0",
        "queries with no positive candidate: "
        + ", ".join(f"{r['bucket']} {r['share']:.1%}" for r in no_pos.sort("bucket").iter_rows(named=True))
        + " (these queries score 0 nDCG for every model)",
        "r is heavy-tailed (unusual, not impossible): kept as is, log1p label",
    ]

    out = {
        "dataset": {
            "train": f"{REL}/pairs_train.parquet",
            "test": f"{REL}/pairs_test.parquet",
            "truth_train": f"{REL}/truth_train.parquet",
            "truth_test": f"{REL}/truth_test.parquet",
            "queries_train": f"{REL}/queries_train.parquet",
            "queries_test": f"{REL}/queries_test.parquet",
            "months": f"{REL}/months/",
            "label": "label", "id": ["q", "item"], "group": "q", "raw_count": "r",
            "split": {
                "type": "cutoff",
                "train_cutoff": "2026-08-01", "test_cutoff": "2026-09-01",
                "horizon_days": 30, "feature_window_days": 31, "seed": 42,
                "train_features": "2026-07", "train_labels": "2026-08",
                "test_features": "2026-08", "test_labels": "2026-09",
            },
            "exclusions": [
                "type external (search, empty referrer, other sites) as source",
                "Main_Page as source or candidate",
                "self pairs (q = item)",
                "pairs with n < 10 a month (upstream Wikimedia filter; min n = 10)",
                "bot traffic (upstream Wikimedia filter, user agents)",
            ],
            "built_by": "modeling/build_dataset.py",
        },
        "shape": {
            "rows": df.height, "columns": len(pairs.columns),
            "memory_mb": round(pairs.estimated_size("mb"), 1),
        },
        "nulls": {c: round(float(pairs[c].null_count() / pairs.height), 4) for c in pairs.columns},
        "target": {
            "column": "label", "type": "regression",
            "class_balance": {"label > 0": stats["train"]["positive_rate"],
                              "label = 0": round(1 - stats["train"]["positive_rate"], 4)},
            "distribution": {
                "label": num_profile(df["label"]),
                "label_where_positive": num_profile(df.filter(pl.col("r") > 0)["label"]),
                "r_where_positive": num_profile(df.filter(pl.col("r") > 0)["r"]),
                "r_quantiles_positive": {
                    str(p): float(df.filter(pl.col("r") > 0)["r"].quantile(p))
                    for p in (0.5, 0.9, 0.99, 0.999)
                },
                "positive_rate_by_bucket": pos_by_bucket,
            },
        },
        "numeric_distributions": {
            "candidates_per_query": num_profile(per_q["n_cand"]),
            "positives_per_query": num_profile(per_q["n_pos"]),
            "src_out_f (query, feature month)": num_profile(q["src_out_f"]),
        },
        "categorical_distributions": {
            "bucket (pairs)": {
                "cardinality": df["bucket"].n_unique(),
                "top_values": {r["bucket"]: r["len"] for r in df.group_by("bucket").len().iter_rows(named=True)},
            },
            "candidate source (share of pairs)": {"cardinality": len(flags), "top_values": flag_rates},
            "candidate source (positive rate)": {"cardinality": len(flags), "top_values": flag_pos},
        },
        "candidate_recall_train": stats["train"]["candidate_recall"],
        "candidate_recall_test": stats["test"]["candidate_recall"],
        "build_stats": stats,
        "quality_flags": quality,
    }
    (HERE / "01-data.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({k: out[k] for k in ("shape", "target", "numeric_distributions",
                                           "categorical_distributions", "quality_flags")}, indent=2))


if __name__ == "__main__":
    main()
