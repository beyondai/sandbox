prd-hash: 9374c6c61a3b222e4405e6d4ce82be7300454fbe
high-level-hash: 55dd513885ee3e44854cb0d65aa2b29170730701

# Spec: kkbox-recommendation

## Problem Statement

Build the best POC recommendation-signal system for the WSDM/KKBOX
repeat-listen prediction task, maximizing predictive quality (AUC) on
held-out data. Not tied to a specific business pain point (e.g. cold
start) - just the strongest offline classifier this exercise can
produce.

## Solution

Pointwise binary classification: predict P(repeat listen = 1) for a
(msno, song_id) pair, where target = 1 if the user listens to that
song again within 1 month after their first observable listen in the
dataset's collection window. Scoring is a single offline batch pass
over the competition's `test.csv` (no online/live population or
cadence). Unit of prediction: one (user, song) row joined with that
user's member attributes and that song's metadata as of the row's
snapshot time. This folder builds exactly one model (the classifier
above) - no second model.

Architecture: fully offline/batch. Source tables (KKBOX WSDM 2018
dataset): `train.csv`, `test.csv`, `members.csv`, `songs.csv`,
`song_extra_info.csv`, unzipped from
`data/kkbox/kkbox-music-recommendation-challenge.zip` into
`data/kkbox/extracted/`. No online-inference path is built in this
project (see `design/high-level.md`'s online diagram, marked
hypothetical/out of scope).

## Implementation Decisions

- V0 (this project) model class: baseline - logistic regression or a
  single small tree ensemble, trained once, no hyperparameter search
  (`design/high-level.md`, Phasing).
- Features (V0): simple joins only - song length, genre, language,
  song-name/artist metadata, member city, age, registration method,
  membership expiry, plus time-safe aggregate counts (e.g. prior
  plays of this song by this user).
- Framing: pointwise binary classification chosen over
  learning-to-rank, because the competition's own metric (AUC on
  independent per-row probabilities) matches pointwise classification
  directly and the labeled rows aren't naturally grouped into
  per-user candidate lists (`adr/0001-pointwise-classification-over-
  learning-to-rank.md`).
- Exclusions: any listening events for a given (msno, song_id) row
  that occur after that row's label window must be excluded from
  feature computation, to avoid label leakage. A time-based split
  would normally follow for the same reason, but this dataset has no
  row-level timestamp to cut on (see `01-data.md`), so a random,
  class-stratified split (seed 42) is used instead - leakage is
  still avoided because no column exposes post-label-window events.

## Testing Decisions

- Primary offline metric: AUC (area under the ROC curve) between
  predicted probability and observed target - matches the
  competition's own evaluation metric directly (PRD, Metrics -
  Offline).
- No online metrics or guardrails apply - this is an offline-only POC
  (PRD, Metrics - Online: N/A).
- Split rule: random, class-stratified 80/20 split (seed 42), decided
  by `ml-modeling-data` - not a time-based cutoff, since this dataset
  has no row-level timestamp to cut on (see `modeling/01-data.md` for
  the full reasoning).

## Out of Scope

Real-time/online serving; integration into a live ranking pipeline;
cross-lingual/catalog-specific embedding work; exploration/bandit
logic; production A/B testing (PRD, Requirements - Scope).
