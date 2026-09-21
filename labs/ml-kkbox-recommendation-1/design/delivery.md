# KKBOX Recommendation - Delivery (Quick POC)

Quick POC mode: each item states its most likely answer in one pass,
flagged as an assumption where noted. This project took the hands-on
route (`ml-modeling-*`), so Eval below cites `modeling/04-evaluate.md`'s
real results rather than a hypothetical eval plan. Everything else in
this section is necessarily hypothetical - `prd/kkbox-recommendation.md`
scoped real-time serving, live ranking integration, and production A/B
testing out of this exercise entirely, so Deployment/Monitoring/Fallback
describe what *would* happen if this POC's model were carried into
production, matching `design/high-level.md`'s own online architecture
diagram, which is marked hypothetical for the same reason.

## Execution

This POC (V0) is complete as of 2026-09-21: data cleaned and profiled,
112 features engineered, 3 model candidates compared (a CV-leakage bug
found and fixed along the way), Random Forest selected, evaluated against
a real held-out test set, and cross-checked against a same-test-set
re-run of the `monkey-mode` baseline. Solo project, one session -
`prd/kkbox-recommendation.md`'s Team section already notes there's no
real team/sprint process for this exercise.

*(assumption, hypothetical V1 milestones)* Carrying this to
`design/high-level.md`'s V1 phase (tuned gradient-boosted trees, richer
listening-history aggregates, reused production matrix-factorization
factors) would follow that phase's own estimate: 2-3 weeks, 1-2 ML
engineers. Milestones within that window: week 1 - full-dataset training
pipeline (this POC used ~8.1% of `train.csv`, see `01-data.md`) and
richer feature set; week 2 - tuning and the shadow-mode deployment below;
week 3 - ramp decision based on shadow results.

## Deployment

*(all hypothetical - out of scope per PRD, described for completeness)*

- **Rollout**: shadow mode first - score in parallel with the existing
  production CF + matrix-factorization + embedding recommender
  (`design/high-level.md`'s Architecture) without affecting what users
  see, comparing this model's scores against real outcomes for 1-2 weeks.
  If shadow metrics hold up, ramp as an additional blended signal (not a
  replacement) starting at 5% of traffic, doubling every few days if
  guardrails hold, per the "blended ranking" architecture already
  sketched - this model was designed from the start to add a signal to
  the existing blend, not replace it.
- **Testing**: unit tests for the feature-engineering pipeline
  (`build_features.py`/`build_test_features.py`) don't exist yet for this
  POC - a real gap, not silently assumed away, and the concrete next
  step before any production work. Integration testing exists in
  practice already: `build_test_features.py` + `model.joblib` scoring
  the real held-out test set *is* an end-to-end integration test, just
  not automated/repeatable as a CI check yet. Load testing doesn't apply
  to this POC's offline batch scoring; it would matter once/if the
  hypothetical online path is built.
- **CI/CD**: none built for this single-session POC. A reasonable next
  step: a scheduled retraining job (the aggregate/target-encoded
  features in `02-features.md` go stale as new users/songs/artists
  appear) plus a CI check that re-runs `build_test_features.py` +
  scoring against a fixed regression fixture before any model swap.

## Eval

Real results, not a hypothetical plan (hands-on route) - full detail in
`modeling/04-evaluate.md`:

- **Offline**: AUC 0.7361 on a genuine held-out test split (never touched
  during feature engineering or model selection). Clears the PRD/
  monkey-mode success bar (AUC >= 0.65) and beats a true same-test-set
  re-run of `monkey-mode/report.md`'s baseline by +0.0615 AUC. Overfit
  gap (train 0.769 -> test 0.736) is modest. Not comparable to the real
  Kaggle leaderboard - see `04-evaluate.md`'s note on why.
- **A/B test design** *(hypothetical - PRD's Metrics - Online section is
  explicitly N/A for this POC)*: if deployed, the online primary metric
  would be repeat-listen rate or session-time lift (per PRD), with skip
  rate as the guardrail that must not regress. Significance method: a
  two-proportion z-test (or sequential testing if the ramp needs an
  early-stop option) on repeat-listen rate between the blended-ranking
  arm and the existing-recommender-only control, powered against the
  offline AUC gap above as a rough effect-size prior.

## Monitoring

Two different things, worth keeping separate:

- **This project's own dashboard** (already built, real):
  `dashboard/app.py` (Streamlit, `http://localhost:8501`) - EDA, model
  comparison, and final results. This monitors the *development
  process*, not a live production system - it has no latency/error-rate
  tracking because there's no live service to track.
- **Hypothetical production monitoring** *(not built, out of scope)*:
  system-health - inference latency and error rate of the scoring
  service; model-health - prediction-score distribution drift over time,
  null-rate drift on `bd`/`gender` (already flagged as risky in
  `01-data.md`), and coverage drift on the `artist_name`/`msno`/`song_id`
  aggregate lookup tables as new entities appear that weren't in the
  ~8.1% training sample (the fallback values in `02-features.md`'s
  "Applying to the test split" - global mean for repeat-rates, 0 for
  frequency encodings - would fire increasingly often as the catalog
  grows past what this POC ever saw, which is itself a metric worth
  tracking).

## Fallback

Most-skipped item, checked first: **on failure or degradation, drop this
model's contribution and let the existing blended ranking continue
without it** - not "revert to a prior model," since this POC was
designed from the start to add one signal to an existing production
recommender (`design/high-level.md`'s Architecture), not replace it. The
existing CF + matrix-factorization + embedding system already works
without this model's input; falling back to it is a null-op, not a
separate rollback plan to build.

- **Trigger**: scoring-service inference error, latency exceeding the
  blended ranker's budget, or a feature-pipeline failure (e.g. a lookup
  table this model depends on - `msno_repeat_rate.csv`,
  `song_repeat_rate.csv`, `artist_repeat_rate.csv`,
  `context_freq.csv`, `genre_primary_top.csv` - fails to load or is
  stale past a freshness threshold).
- **Target**: the existing production recommender's blend, minus this
  model's signal - immediate, no separate "prior model" needed since
  this model never stood alone.

## Change log

- 2026-09-21: initial Delivery section for the Quick POC.
