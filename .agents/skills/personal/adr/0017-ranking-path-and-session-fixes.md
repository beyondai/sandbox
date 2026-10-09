# Ranking path, proxy rule, and other fixes from the Riot wiki session

## Context

The Riot wiki recommender (`labs/ml-riot-wiki-recommender-1`, 2026-10-08
to 2026-10-09) was the first project to run the whole modeling chain on a
ranking task, on proxy data. The session-end reflection (ADR 0016) logged
11 skill issues. The user adopted 8 of them, picking the ones that would
also help other projects (the test: would it have helped
`ml-kkbox-recommendation-1` or `ml-riot-churn-1`?).

## Decision

Adopted:

1. `ml-modeling-train`: a "Ranking tasks" section (folds by query,
   per-query nDCG, graded target, baseline rule on the same folds, no
   threshold) and a LambdaMART row; `ml-modeling-multiagent` points to
   it.
2. `ml-modeling-train`: check that LightGBM or XGBoost loads before using
   it; `libomp` is a system install the user approves.
3. `ml-modeling-evaluate`: a "Ranking" section (full truth, candidate
   recall, query and item segments, bootstrap over queries; parquet for
   large score files).
4. `ml-modeling` router: the chain mode goes to line 3 of the spec, and
   later steps keep it unless the request names a mode.
5. `ml-modeling` router: update the spec lines that cite a changed design
   doc before a hash refresh.
6. `ml-modeling` router: a "Proxy data" section ("For <target>" lines;
   proxy numbers are evidence or a lower bound).
7. `ml-modeling-serve` and `bench_serve.py`: `--full` and `--chunk` time a
   whole batch job; the serve skill also says to cache history tables in
   the feature module (folded in from a declined, narrower entry).
8. `feature_selector.py`: reads parquet, with `--sample` and `--drop`.

Declined:

- Cache history in features, as its own rule: a coding detail; one
  sentence went into the serve skill instead.
- Gate per slice: fits products with clear segments and a cheap
  fallback; it stays a project decision (Riot wiki `adr/0002`).
- New vs rarely-used slices: a recommender default, not general; it
  stays in the Riot wiki PRD.

## Consequences

- A ranking project no longer needs hand-built CV and metrics; the two
  skills name the method.
- `bench_serve.py` output adds `full_batch` (null without `--full`).
- Specs gain a `mode:` line; `spec_hash_check.sh` reads keys, so older
  specs without it still work (a missing line means: use the request's
  keyword, as before).
