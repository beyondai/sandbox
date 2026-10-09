#!/usr/bin/env python3
"""Measure the latency and throughput of a project's serving function.

Usage (from the sandbox root):
  uv run python3 .agents/skills/personal/ml-modeling-serve/scripts/bench_serve.py \
      --serve <project>/modeling/serve.py --rows <test table .csv|.parquet> \
      [--model <project>/modeling/model.joblib] [--single 300] [--warmup 30] \
      [--batch-size 1000] [--batches 5] [--out <file.json>]

`serve.py` must define `score(df) -> scores` (one score per input row). The
script imports it, so the measured path is the real serving path:
  1. Warm-up: `--warmup` single-row calls, not timed (imports, caches, JIT).
  2. Single request: `--single` calls of 1 row each -> p50, p95, p99, max
     in milliseconds (the online latency).
  3. Batch: `--batches` calls of `--batch-size` rows -> rows per second
     (the batch throughput, and the QPS of 1 replica for a 1-row request
     is 1000 / p50_ms).
  4. Size: the model file on disk, if `--model` is given.

Rows are sampled with replacement when the table is smaller than needed.
Prints one JSON object (and writes it to `--out` if given). Exit code 0 on
success, 2 on a usage error, 1 if `score` fails or returns the wrong
number of scores.

Requires: python3, pandas (and pyarrow for .parquet), plus whatever
serve.py imports. In the sandbox: `uv run` from the root (shared venv);
add a missing package with `uv add <pkg>` at the sandbox root.
"""
import argparse
import importlib.util
import json
import math
import os
import platform
import statistics
import sys
import time

# Defaults. Each reason says what the value makes reliable.
# Warm-up calls: the first calls pay for imports, caches, and lazy setup.
# 30 is enough for those costs to stop showing in a CPU model.
WARMUP = 30
# Timed 1-row calls: p99 needs at least 100 samples to mean anything.
# 300 puts about 3 samples above p99.
SINGLE = 300
# Rows per batch call: large enough that the fixed cost of a call is small
# next to the cost per row.
BATCH_SIZE = 1000
# Batch calls: the median of 5 ignores 1 or 2 slow runs.
BATCHES = 5
# Fixed sample seeds, so that a rerun scores the same rows.
SEED_WARMUP, SEED_SINGLE, SEED_BATCH = 0, 1, 100


def load_score(path):
    spec = importlib.util.spec_from_file_location("serve", path)
    if spec is None or spec.loader is None:
        sys.exit(f"{path}: cannot import")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
    spec.loader.exec_module(module)
    if not hasattr(module, "score"):
        print(f"{path}: no score(df) function", file=sys.stderr)
        sys.exit(2)
    return module.score


def load_rows(path):
    import pandas as pd
    if path.endswith(".parquet"):
        return pd.read_parquet(path)
    return pd.read_csv(path)


def percentile(values, q):
    s = sorted(values)
    k = (len(s) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def call(score, df):
    out = score(df)
    if len(out) != len(df):
        print(f"score returned {len(out)} values for {len(df)} rows",
              file=sys.stderr)
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--serve", required=True)
    ap.add_argument("--rows", required=True)
    ap.add_argument("--model")
    ap.add_argument("--single", type=int, default=SINGLE)
    ap.add_argument("--warmup", type=int, default=WARMUP)
    ap.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    ap.add_argument("--batches", type=int, default=BATCHES)
    ap.add_argument("--out")
    args = ap.parse_args()
    for p in (args.serve, args.rows):
        if not os.path.isfile(p):
            print(f"{p}: not found", file=sys.stderr)
            return 2

    score = load_score(args.serve)
    rows = load_rows(args.rows)
    if rows.empty:
        print(f"{args.rows}: no rows", file=sys.stderr)
        return 2

    def sample(n, seed):
        return rows.sample(n=n, replace=len(rows) < n, random_state=seed)

    warm = sample(args.warmup, SEED_WARMUP)
    for i in range(len(warm)):
        call(score, warm.iloc[[i]])

    single = sample(args.single, SEED_SINGLE)
    times = []
    for i in range(len(single)):
        row = single.iloc[[i]]
        t0 = time.perf_counter()
        call(score, row)
        times.append((time.perf_counter() - t0) * 1000)

    batch_rates = []
    for b in range(args.batches):
        df = sample(args.batch_size, SEED_BATCH + b)
        t0 = time.perf_counter()
        call(score, df)
        batch_rates.append(len(df) / (time.perf_counter() - t0))

    p50 = percentile(times, 0.50)
    result = {
        "single_requests": len(times),
        "p50_ms": round(p50, 3),
        "p95_ms": round(percentile(times, 0.95), 3),
        "p99_ms": round(percentile(times, 0.99), 3),
        "max_ms": round(max(times), 3),
        "qps_per_replica_1_worker": round(1000 / p50, 1) if p50 > 0 else None,
        "batch_size": args.batch_size,
        "batch_rows_per_sec": round(statistics.median(batch_rates), 1),
        "model_mb": (round(os.path.getsize(args.model) / 1e6, 3)
                     if args.model and os.path.isfile(args.model) else None),
        "machine": f"{platform.machine()} {platform.system()}, "
                   f"{os.cpu_count()} CPUs, python {platform.python_version()}",
    }
    text = json.dumps(result, indent=2)
    print(text)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
