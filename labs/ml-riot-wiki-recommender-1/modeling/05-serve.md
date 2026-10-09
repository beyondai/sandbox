# 05 - Serve

- Mode: Quick POC (the chain's mode), 2026-10-09.
- Design docs: the spec hashes match the current PRD and
  `design/high-level.md`.
- Evaluate verdict: **partial** (`04-evaluate.json`). Quick POC goes on.
  The served ranker is the per-slice hybrid, the part that passed.
- Code: `modeling/serve.py` (`score(df)`). Benchmark:
  `modeling/05-bench.json`. Machine: the laptop (Intel i7-10700K, 16
  threads, macOS), **not the production machine**.
- Proxy rule: as in `01-data.md`. Riot numbers are scaled from the proxy
  and marked as assumptions.

## Mode: batch precompute, online lookup

- **Reason (cadence).** The ranking for page A depends only on A and on
  history that changes slowly (opened-next counts over 28 days, links,
  text). It does not depend on the viewer in V1. The PRD allows 24-hour
  freshness for new and edited pages. So the model runs in a nightly
  batch, and the request path only reads the result.
- **Only permissions are request-time.** They depend on the viewer and
  must apply with no delay (PRD), so the filter runs online, after the
  lookup.
- **Measured reason not to score online:** a 1-row call of `score()` takes
  522 ms at p50 and 572 ms at p99 on the laptop, against a 150 ms p99
  target for the whole panel. A per-request model is not needed and would
  not fit.

```
nightly batch (offline)                         request (online)
candidates (up to 100 per page)                 reader opens page A
  -> transform() -> model / V0 routing            -> KV get recs[A] (top 20)
  -> top 20 per page -> KV store  ------------>   -> permission + status filter
                                                  -> top 5 -> panel
```

## Stages and candidates

- Batch: candidate generation, up to 100 candidates per page (proxy: 53
  on average; rules: opened-next, two-hop, reverse, popular; Riot adds
  links, page tree, entities, embedding nearest pages, borrowed clicks).
- Batch: ranking of all candidates (`score()`), keep the top 20.
- Online: read the top 20, drop pages the viewer can't access and
  archived pages, keep the top 5. V2 adds the exploration slot here.
- The top 20 leaves room for the filter: 15 pages can be dropped before
  the panel shows fewer than 5.

## Latency budget (online path, PRD p99 150 ms)

The model is not on the request path. Budget for the Recs API
(assumptions until the Delivery load test):

- network and wiki UI call: 25 ms;
- KV lookup `recs[A]`: 10 ms;
- permission check, cached per viewer and space: 50 ms (a cache miss
  calls the wiki permissions API);
- page status check (cached): 10 ms;
- exploration slot (V2): 5 ms;
- serialization: 5 ms;
- slack: 45 ms (30%).

KV miss (a page created since the last batch): the day-one rule runs on
request (out-links + back-links + siblings, ranked by views). It reads
indexes, not the model; budget 40 ms from the slack. Not measured here.

## Features at serving time

- `serve.py` calls `transform()` from `features.py`, the training code.
  No feature logic is copied, so there is no training-serving skew.
- Parity check: `score()` on all 3,150,603 test pairs equals the
  `hybrid` scores from `evaluate.py` exactly (max difference 0.0).
- `features.py` now caches the loaded history window per process
  (`history()`, `page_age()`), because a serving process calls
  `transform()` many times. The feature values did not change (the parity
  check above).
- Online, no features are computed: the request reads precomputed ranks.
- **For Riot:** the batch also runs the text pipeline for new and edited
  pages (about 1.1k a week): embeddings, entities, near-duplicate groups.
  Log the features used in each batch, so the next training set uses the
  same values.

## Model format, size and hardware

- scikit-learn `HistGradientBoostingRegressor` in joblib: **0.38 MB** on
  disk. Load time 1.8 s at import (includes the feature code).
- CPU only. No GPU: 100 trees on 23 dense features.
- **For Riot:** the embedding model (about 30M parameters) also runs on
  CPU in the batch; minutes for a full backfill of 40k pages (assumption).

## Measured (`bench_serve.py`, laptop)

- Single-row request: p50 522 ms, p95 557 ms, p99 572 ms, max 582 ms (200
  requests after 20 warm-up). QPS of 1 worker: 1.9.
- Batch of 1,000 random rows: 1,789 rows per second.
- Whole batch in one call (all 3,150,603 test pairs, 59,612 pages):
  5.2 s, **607,009 rows per second**; 4.1 s on a second call with the
  history cached.
- Why the small calls are slow: each call joins its rows against the full
  history window (22.8M pairs). The cost is per call, not per row. The
  batch job must call `score()` once per large chunk (100k+ rows), never
  per page.

## Capacity

### Batch (nightly)

`job time = scoring population / throughput`

- Riot population: 40k pages x 100 candidates = 4.0M pairs (PRD, upper
  bound).
- Throughput: 607k rows per second (laptop, 1 process).
- Ranking time: 4.0M / 607k = **about 7 s**. With candidate generation
  and the text pipeline: under 10 minutes (assumption).
- Window: a 6-hour nightly window (assumption). The job uses under 3% of
  it; target is under 50%.

### Online (Recs API)

`replicas = ceil(peak QPS x (1 - cache hit rate) / QPS per replica x headroom)`

- Peak QPS: 50 (PRD).
- Cache hit rate: 0 (counted as misses; the KV store is the cache).
- QPS per replica: 500 for a KV read plus a cached permission check
  (assumption; not measured: the path has no model).
- Headroom: 1.5.
- `ceil(50 x 1 / 500 x 1.5) = ceil(0.15) = 1`. Run **2 replicas**, so one
  can fail (99.5% availability, PRD).
- Comparison: scoring online with the model at 1.9 QPS per worker would
  need `ceil(50 / 1.9 x 1.5) = 40` workers and still miss the p99.

### Degradation under overload

1. Drop the exploration slot (V2+).
2. On a KV miss, return the space's most-read pages (cached) in place of
   the on-request day-one rule.
3. If the nightly batch fails, keep serving the last good batch (scores
   age by one day; alert after 2 missed nights).
4. If the API is down or over budget, hide the panel; the page works as
   normal (PRD).

## Cost (assumptions: unknown prices)

- Batch: about 10 CPU-minutes a night. At $0.05 per vCPU-hour: under
  $0.01 a run, under $1 a month.
- KV store: 40k pages x 20 recs x about 50 bytes = about 40 MB.
- Online: 2 small replicas (0.5 vCPU, 1 GB each): about $30-60 a month.
- Per 1,000 requests at peak: 50 QPS is 4.3M requests a day; at about
  $2 a day for the replicas, about $0.0005 per 1,000 requests.
- Compared with the value (engineer time saved finding docs), the cost is
  negligible. The real cost is maintenance: the nightly job, the text
  pipeline and the weekly retrain.

## Verdict

**Meets the p99 target by design, not by model speed.** The 150 ms p99
applies to the online path, which is a KV read and a cached permission
filter; the model runs in a nightly batch that needs about 7 s of ranking
time for Riot's 4M pairs. The measured 572 ms p99 for a 1-row model call
shows why the model must stay off the request path. The online numbers are
assumptions until the Delivery load test runs at 50 QPS with 2 replicas.

## Change log

- 2026-10-09: created.
