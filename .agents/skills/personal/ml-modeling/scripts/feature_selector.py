#!/usr/bin/env python3
"""Score and rank features for predictive modeling using standard-library-only methods.

Computes feature importance via variance, correlation with target, cardinality,
null rate, and information-theoretic measures.  Produces a ranked list with
composite scores to guide feature selection.

Requires: python3 standard library only (no venv needed) for a CSV file.
A .parquet file needs pandas and pyarrow: run it with `uv run python3`
from the sandbox root (the shared venv has both).

Usage:
    python feature_selector.py --file dataset.csv --target churn
    python feature_selector.py --file dataset.csv --target revenue --top 10 --json
    python feature_selector.py --file dataset.csv --target label --method all
    uv run python3 feature_selector.py --file train.parquet --target label \
        --sample 200000 --drop q,item
"""

import argparse
import csv
import json
import math
import os
import random
import sys
from collections import Counter

# Thresholds and weights. Each is a heuristic for a first ranking, not a
# tuned value; the reason says what it protects against.

# A column is numeric when more than 80% of its non-null values parse as
# numbers. Reason: a few stray tokens ("N/A", "-") must not make it text.
NUMERIC_SHARE = 0.8
# A text column with more than 95% distinct values is likely an ID. Below
# 50 rows, a high distinct share happens by chance, so do not flag it.
ID_DISTINCT_SHARE = 0.95
ID_MIN_ROWS = 50
# A text column with under 1 distinct value per 100 rows is nearly constant.
CONSTANT_DISTINCT_SHARE = 0.01
# Score for an ID-like or nearly constant column. Low, but not 0, so the
# column stays in the ranking for a person to review.
PENALTY_SCORE = 0.1
# Cardinality score = distinct share * 5, capped at 1. Reason: a column
# with 20% or more distinct values gets the full score.
DISTINCT_SCALE = 5
# Correlation needs more than 5 numeric pairs. Reason: with fewer pairs,
# |r| is mostly noise.
MIN_CORR_PAIRS = 5
# Equal-width bins for mutual information on numeric columns. Reason: 10
# bins show the shape and keep about 10% of the rows in each bin.
MI_BINS = 10
# Composite weights. Correlation and mutual information measure the link
# to the target, so they weigh most. Null rate and variance measure only
# data quality.
WEIGHTS = {
    "null_completeness": 0.15,
    "variance": 0.20,
    "cardinality": 0.20,
    "abs_correlation": 0.35,
    "mutual_info": 0.30,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_numeric(value: str) -> bool:
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def _to_floats(values: list) -> list:
    return [float(v) for v in values if _is_numeric(str(v)) and str(v).strip()]


def _mean(vals: list) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _std(vals: list) -> float:
    if len(vals) < 2:
        return 0.0
    m = _mean(vals)
    return math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))


def _correlation(x: list, y: list) -> float:
    """Pearson correlation coefficient."""
    n = min(len(x), len(y))
    if n < 3:
        return 0.0
    mx, my = _mean(x[:n]), _mean(y[:n])
    sx, sy = _std(x[:n]), _std(y[:n])
    if sx == 0 or sy == 0:
        return 0.0
    cov = sum((x[i] - mx) * (y[i] - my) for i in range(n)) / (n - 1)
    return cov / (sx * sy)


def _entropy(values: list) -> float:
    """Shannon entropy in bits."""
    counts = Counter(values)
    total = len(values)
    if total == 0:
        return 0.0
    ent = 0.0
    for c in counts.values():
        p = c / total
        if p > 0:
            ent -= p * math.log2(p)
    return ent


def _mutual_information(feature_vals: list, target_vals: list) -> float:
    """Approximate mutual information using discrete bins."""
    n = len(feature_vals)
    if n == 0:
        return 0.0

    # Bin numeric features into MI_BINS bins
    joint = Counter(zip(feature_vals, target_vals))
    f_counts = Counter(feature_vals)
    t_counts = Counter(target_vals)

    mi = 0.0
    for (f, t), joint_count in joint.items():
        p_joint = joint_count / n
        p_f = f_counts[f] / n
        p_t = t_counts[t] / n
        if p_joint > 0 and p_f > 0 and p_t > 0:
            mi += p_joint * math.log2(p_joint / (p_f * p_t))
    return mi


def _bin_numeric(values: list, bins: int = MI_BINS) -> list:
    """Bin numeric values into discrete categories."""
    floats = _to_floats(values)
    if not floats:
        return values  # non-numeric, return as-is
    mn, mx = min(floats), max(floats)
    if mn == mx:
        return ["bin_0"] * len(values)
    step = (mx - mn) / bins
    result = []
    for v in values:
        if _is_numeric(str(v)):
            idx = min(int((float(v) - mn) / step), bins - 1)
            result.append(f"bin_{idx}")
        else:
            result.append("NA")
    return result


# ---------------------------------------------------------------------------
# Feature scoring
# ---------------------------------------------------------------------------

def score_features(data: list, target_col: str, method: str = "all") -> list:
    if not data:
        return []

    columns = [c for c in data[0].keys() if c != target_col]
    target_values = [row.get(target_col, "") for row in data]
    target_numeric = _to_floats(target_values)
    target_is_numeric = len(target_numeric) > len(target_values) * NUMERIC_SHARE

    results = []

    for col in columns:
        raw_values = [row.get(col, "") for row in data]
        total = len(raw_values)
        non_null = [v for v in raw_values if v is not None and str(v).strip()]
        null_count = total - len(non_null)
        null_rate = null_count / total if total > 0 else 0

        score_components = {}

        # 1. Null rate score (lower nulls = better)
        null_score = max(0, 1.0 - null_rate)
        score_components["null_completeness"] = round(null_score, 4)

        # 2. Variance / cardinality score
        numeric_vals = _to_floats(raw_values)
        is_numeric = len(numeric_vals) > len(non_null) * NUMERIC_SHARE if non_null else False

        if is_numeric and numeric_vals:
            std = _std(numeric_vals)
            mean_abs = abs(_mean(numeric_vals))
            cv = std / mean_abs if mean_abs > 0 else std
            var_score = min(1.0, cv)  # Cap at 1.0
            score_components["variance"] = round(var_score, 4)
        else:
            unique = len(set(str(v) for v in non_null))
            card_ratio = unique / len(non_null) if non_null else 0
            # Penalize very low (constant) and very high (unique ID) cardinality
            if card_ratio > ID_DISTINCT_SHARE and len(non_null) > ID_MIN_ROWS:
                var_score = PENALTY_SCORE  # Likely a unique ID
            elif card_ratio < CONSTANT_DISTINCT_SHARE:
                var_score = PENALTY_SCORE  # Nearly constant
            else:
                var_score = min(1.0, card_ratio * DISTINCT_SCALE)
            score_components["cardinality"] = round(var_score, 4)

        # 3. Correlation with target (numeric features vs numeric target)
        if is_numeric and target_is_numeric and method in ("all", "correlation"):
            # Align lengths
            paired = []
            for row in data:
                fv, tv = row.get(col, ""), row.get(target_col, "")
                if _is_numeric(str(fv)) and _is_numeric(str(tv)):
                    paired.append((float(fv), float(tv)))
            if len(paired) > MIN_CORR_PAIRS:
                fx, fy = zip(*paired)
                corr = abs(_correlation(list(fx), list(fy)))
                score_components["abs_correlation"] = round(corr, 4)

        # 4. Mutual information (works for both numeric and categorical)
        if method in ("all", "mutual_info"):
            feat_binned = _bin_numeric(raw_values) if is_numeric else [str(v) for v in raw_values]
            tgt_binned = _bin_numeric(target_values) if target_is_numeric else [str(v) for v in target_values]
            mi = _mutual_information(feat_binned, tgt_binned)
            # Normalize by target entropy
            t_ent = _entropy(tgt_binned)
            mi_normalized = mi / t_ent if t_ent > 0 else 0
            score_components["mutual_info"] = round(min(1.0, mi_normalized), 4)

        # Composite score (weighted average)
        total_weight = 0
        weighted_sum = 0
        for key, value in score_components.items():
            w = WEIGHTS[key]
            weighted_sum += value * w
            total_weight += w
        composite = weighted_sum / total_weight if total_weight > 0 else 0

        results.append({
            "feature": col,
            "composite_score": round(composite, 4),
            "data_type": "numeric" if is_numeric else "categorical",
            "null_rate": round(null_rate, 4),
            "unique_values": len(set(str(v) for v in non_null)),
            "scores": score_components,
        })

    results.sort(key=lambda x: x["composite_score"], reverse=True)
    return results


# Seed for --sample, so that a rerun ranks the same rows.
SAMPLE_SEED = 42


def load_rows(path, sample=None, drop=()):
    """Rows as dicts of strings (the CSV reader's shape), from .csv or
    .parquet, optionally a seeded sample, without the dropped columns."""
    if path.endswith(".parquet"):
        import pandas as pd  # only for parquet; see Requires
        df = pd.read_parquet(path)
        if sample and sample < len(df):
            df = df.sample(n=sample, random_state=SAMPLE_SEED)
        df = df.drop(columns=[c for c in drop if c in df.columns])
        df = df.astype(object).where(df.notna(), "")
        return [{k: str(v) for k, v in row.items()} for row in df.to_dict("records")]
    with open(path, "r", newline="") as f:
        data = list(csv.DictReader(f))
    if sample and sample < len(data):
        data = random.Random(SAMPLE_SEED).sample(data, sample)
    return [{k: v for k, v in row.items() if k not in drop} for row in data]


def main():
    parser = argparse.ArgumentParser(description="Score and rank features for predictive modeling.")
    parser.add_argument("--file", required=True, help="Path to a .csv or .parquet data file")
    parser.add_argument("--target", required=True, help="Target column name")
    parser.add_argument("--top", type=int, help="Show only top N features")
    parser.add_argument("--method", choices=["all", "correlation", "mutual_info"], default="all", help="Scoring method (default: all)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--sample", type=int, help="Score a seeded sample of N rows (large tables)")
    parser.add_argument("--drop", default="", help="Comma-separated columns to leave out (id columns)")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    drop = [c for c in args.drop.split(",") if c]
    data = load_rows(args.file, args.sample, drop)

    if not data:
        print("Error: No data rows found.", file=sys.stderr)
        sys.exit(1)

    if args.target not in data[0]:
        print(f"Error: Target column '{args.target}' not found. Available: {', '.join(data[0].keys())}", file=sys.stderr)
        sys.exit(1)

    results = score_features(data, args.target, args.method)
    if args.top:
        results = results[: args.top]

    if args.json:
        print(json.dumps({"target": args.target, "method": args.method, "features": results}, indent=2))
    else:
        print(f"Feature Importance Ranking (target: {args.target})")
        print("=" * 70)
        print(f"{'Rank':<6} {'Feature':<25} {'Score':<8} {'Type':<12} {'Nulls':<8} {'Unique'}")
        print("-" * 70)
        for i, r in enumerate(results, 1):
            print(f"{i:<6} {r['feature']:<25} {r['composite_score']:<8} {r['data_type']:<12} {r['null_rate']:<8} {r['unique_values']}")
        print()
        if results:
            print("Top feature details:")
            top = results[0]
            for k, v in top["scores"].items():
                print(f"  {k}: {v}")

    sys.exit(0)


if __name__ == "__main__":
    main()
