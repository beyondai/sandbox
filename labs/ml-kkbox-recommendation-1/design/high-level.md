# KKBOX Recommendation - High-level Design (Quick POC)

Quick POC mode: each item below states its most likely answer in one
pass, flagged as an assumption where noted. Correct anything that's
off before we move on.

## ML framing

**One sentence**: predict, per (user, song) pair, the probability
that the user listens to that song again within a fixed horizon
after their first observable listen - a binary classification
problem, not ranking or regression. *(assumption: framed as
pointwise classification rather than learning-to-rank, since the
Kaggle task itself scores a per-row probability against AUC, not a
ranked list - see the ADR offer below.)*

This folder builds: one binary classifier (repeat-listen probability
model). No second model is implied by this framing.

- **Prediction target**: P(repeat listen = 1) for a given (msno,
  song_id) pair.
- **Label definition and horizon**: target = 1 if the user has at
  least one more listen of that song within 1 month after their
  first observable listening event in the dataset's collection
  window; 0 otherwise. *(assumption: 1-month horizon, matching the
  WSDM/KKBOX competition's own label construction.)*
- **Scoring population and cadence**: every (msno, song_id) row
  present in the competition's `test.csv` - a fixed, one-time batch
  scoring pass over a static historical snapshot, not a recurring
  online population. No cadence beyond "once, offline," per the
  PRD's non-functional requirements.
- **Unit of prediction**: one row = one (user, song) pair, joined
  with that user's member attributes and that song's metadata as of
  the row's snapshot time.
- **Known exclusions / contamination risks**: any listening events
  for a given (msno, song_id) row that occur *after* the label
  window must be excluded from feature computation for that row -
  otherwise aggregate features (e.g. "times this user replayed this
  song") leak the label. Time-based train/held-out split is required
  for the same reason, not a random split. *(assumption; to be
  verified once the raw log schema is inspected during EDA.)*

## Architecture

Two diagrams: how this would be served online if it were shipped
(hypothetical - out of scope per the PRD, shown for completeness),
and the offline training/scoring path this project actually
exercises.

### Offline training (what this project actually builds)

```
kkbox-music-recommendation-challenge.zip
        |
        v
  unzip -> train.csv, test.csv, members.csv,
           songs.csv, song_extra_info.csv
        |
        v
  load + clean (drop/median-impute nulls)
        |
        v
  join train.csv <- members.csv (on msno)
                  <- songs.csv, song_extra_info.csv (on song_id)
        |
        v
  time-safe feature engineering
  (scale numerics, one-hot low-cardinality categoricals,
   aggregate features computed from pre-label-window data only)
        |
        v
  time-based train / held-out split
        |
        v
  train one baseline model (logistic regression or
  single small GBM)
        |
        v
  evaluate: AUC on held-out split
        |
        v
  serialized model artifact + report.md
```

### Online inference (hypothetical - not built in this POC)

```
client app
    |
    v
recommendation service (existing prod system)
    |
    +--> feature store: user profile, song metadata,
    |    recent listening context
    |
    +--> [this model] scores repeat-listen probability
    |
    +--> existing CF + matrix-factorization + embedding
    |    scorer (production system, per PRD's Team - Reuse
    |    hypothetical)
    |
    v
blended ranking -> ranked list returned to client
```

## Phasing

- **V0 (this project, POC)**
  - Features: simple joins only - song length, genre, language,
    song-name/artist metadata, member city, age, registration
    method, membership expiry; plus a handful of time-safe
    aggregate counts (e.g. prior plays of this song by this user).
  - Model class: baseline - logistic regression or a single small
    tree ensemble, trained once, no hyperparameter search.
  - Timeline: hours, same session (matches monkey-mode's baseline
    run).
  - Headcount: 1 (solo practice project).
  - **Validated**, not just assumed: `monkey-mode/report.md` ran
    exactly this shape - a same-day, untuned `RandomForestClassifier`
    on a 600k-row sample (8% of the full 7.4M-row `train.csv`) -
    and reached AUC 0.6727 on an 80/20 held-out split, clearing the
    PRD's 0.65 success bar. Confirms the (user, song) repeat-listen
    problem has real learnable structure at this feature depth,
    before any of `ml-modeling-features`'s richer aggregate/context
    features were added.

- **V1 (first real model)**
  - Features: richer listening-history aggregates with proper
    time-decay, song co-occurrence stats, and the existing
    production system's matrix-factorization latent factors reused
    as input features (per PRD's Team - Reuse).
  - Model class: tuned gradient-boosted trees (LightGBM/XGBoost)
    with cross-validation. No longer a bare assumption:
    `monkey-mode/report.md` recommended this explicitly - same
    model family as the V0 baseline (handles the same mixed
    categorical/numeric, null-heavy feature set), but typically
    extracts more signal per feature and trains fast enough to use
    the full multi-million-row dataset rather than V0's 8% sample.
  - Timeline: 2-3 weeks. *(assumption)*
  - Headcount: 1-2 ML engineers. *(assumption)*

- **V2 (stretch)**
  - Features: sequential listening behavior (session-level
    sequences), blended with the existing CF + embedding recommender
    as a re-ranking signal rather than a standalone score.
  - Model class: two-tower or sequence model (e.g. GRU4Rec-style),
    plus online A/B test infrastructure to validate the blend.
  - Timeline: 1-2 quarters. *(assumption)*
  - Headcount: 2-3 (ML + platform). *(assumption)*

## Change log

- 2026-09-21: added `monkey-mode/report.md`'s validated results to V0
  and V1's model-class bullets (AUC 0.6727 baseline, GBM
  recommendation) - grounding what were bare assumptions in real
  evidence. No ML framing, architecture, or phase structure changed;
  `spec/kkbox-recommendation.md`'s `high-level-hash` refreshed
  accordingly.
