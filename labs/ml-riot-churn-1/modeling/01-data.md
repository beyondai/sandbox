# Riot Churn - Step 1: Data

Mode: Quick POC.

## Dataset

Built by `modeling/build_dataset.py` from three lifecycle source tables
(`players.csv`, `activity.csv`, `purchases.csv`), matching
`design/high-level.md`'s Architecture. `campaign.csv` and
`content_calendar.csv` are excluded, also per that diagram.

**Label**: `_truth/players_truth.csv`'s `state_at_cutoff`, collapsed to
binary - active = 0 (stayed), lapsed or churned = 1 (left). That truth file
is generated at a single global `cutoff_day=180` (see
`_truth/params.csv`) shared by every player - it is not a per-player
relative horizon on its own.

**Feature cutoff and the split rule**: `design/high-level.md`'s ML framing
specifies a 60-day forward horizon. Because the label is anchored to the
fixed day 180, that horizon is implemented as: build features from activity
and purchases strictly before day 120, and use the day-180 label as the
60-days-later outcome (120 + 60 = 180). This was not the first draft. The
first draft used day 180 for both features and the label (the naive reading
of "one global snapshot") - the monkey-mode baseline for this same project
ran that way and got a near-tautological result (ROC-AUC 0.99, dominated by
recency features which trivially separate "already stopped playing" from
"still playing" when both are measured on the same day). Moving the feature
cutoff 60 days earlier fixes this by construction and is also just a more
faithful implementation of the horizon high-level.md already specifies.

Because the whole dataset is anchored to one global cutoff day rather than a
rolling window of many scoring dates, there is no second, later cutoff
available to hold out a temporally separate test set (the classic
train-cutoff / test-cutoff-with-a-full-horizon-of-headroom scheme from the
step's own instructions assumes rolling production logs, not a single
synthetic snapshot). The split used instead is a **random 80/20 split of
players, stratified on the label, fixed seed 42** - the reasonable
substitute when only one snapshot exists. This is a known limitation of
practicing on this synthetic snapshot rather than continuous production
logs; a real deployment would use the rolling scheme once continuous history
exists.

**Population and exclusions**: scoring population is players with at least
14 days of tenure by the day-120 feature cutoff, i.e. signed up on or before
day 106 (excludes players who had not signed up yet by day 120, and those in
the 14-day onboarding grace period named in high-level.md's exclusions).
This excluded 2,971 of the raw 12,000 players (24.8%). `campaign.csv`'s
comeback offer is sent on day 180 for every recipient (verified: `send_day`
is 180 in all 3,150 rows) - strictly after both the day-120 feature cutoff
and would-be contamination window, so no timing-based leakage risk exists
even though the column is excluded regardless per scope.

Row counts: 12,000 raw players -> 9,029 after the grace-period exclusion ->
7,224 train / 1,805 test (80/20, stratified, seed 42).

## Profile (train table only)

**Shape**: 7,224 rows, 19 columns, ~1.2 MB in memory.

**Nulls**: every column is 0% null except `region` at 29.5% (2,132 / 7,224).
That matches the raw source's null rate (players.csv: 3,521 / 12,000,
29.3%), so it is a real "unknown region" segment in the source data, not an
artifact of the join or the feature build.

**Target**: binary, class balance 2,414 stayed (33.4%) / 4,810 left (66.6%)
in train (test is the same by construction of the stratified split). Left
is the majority class - moderate imbalance, not degenerate; F1 alongside
ROC-AUC (per the PRD) is the right pairing rather than accuracy alone.

**Feature distributions** (train):
- `tenure_at_scoring`: 14-120 days, mean 94.9, left-skewed (skew -1.02) -
  most scored players are close to the full 120-day tenure ceiling, since
  the grace-period cutoff removes the newest signups.
- `active_days`, `total_games`, `total_wins`, `total_minutes`: all
  right-skewed (skew ~0.78-0.82), a long tail of heavy players over a large
  mass of light/occasional ones - typical engagement-metric shape.
- `total_party_games`: more skewed still (1.83) - most players never party
  up.
- `win_rate`: roughly centered (mean 0.48, mild left skew -0.72), as
  expected for a matchmade game.
- `days_since_last_active`: right-skewed (0.80), mean 37 days out of a
  120-day window - most players who are going to go quiet within the window
  do so well before its end, which is exactly the recency signal the
  horizon change (above) is designed to make a real predictive feature
  again rather than a tautology.
- `activity_trend` (second-half minus first-half games in the feature
  window): centered near 0 (mean 3.3), roughly symmetric (skew 0.11) - a
  believably neutral trend feature.
- `total_spend`, `purchase_count`, `distinct_item_types`: heavily
  right-skewed (skew 7-8.2) - see quality flags below, only 8.6% of scored
  players purchased anything pre-cutoff.
- `days_since_last_purchase`: left-skewed (-0.85), mean 89.9 out of 120 -
  dominated by the "never purchased" sentinel (filled to the player's full
  tenure at scoring), which is expected given how sparse purchases are.

**Categorical distributions** (train): `region` has 4 known values (EUW
2,197, BR 1,130, KR 1,086, LATAM 679) plus the null segment (2,132).
`platform` is 2 values (pc 5,824, mobile 1,400). `acquisition_source` is 3
values (organic 3,604, paid_ads 2,152, friend_referral 1,468). All
low-cardinality, straightforward for one-hot encoding in the next step.

**Quality flags**:
- `region` null rate (29.5%) exceeds the ~20% risk threshold. This is a
  real "unknown region" segment already present in the raw source, not a
  join bug - the features step should treat it as its own category rather
  than imputing a guessed region or dropping the column.
- `total_spend`, `purchase_count`, and `distinct_item_types` are sparse and
  heavily skewed (only 8.6% of scored players purchased pre-cutoff).
  Suggest a binary `has_purchased` flag plus a log-transform of
  `total_spend` in the features step, rather than feeding the raw skewed
  values directly into a linear model.
- The feature cutoff was moved from day 180 to day 120 specifically because
  same-day features made the label near-tautological in the monkey-mode
  run for this project (ROC-AUC 0.99, recency-dominated). This build avoids
  that by construction - see Dataset section above for the reasoning.
- 24.8% of the raw population was excluded as too new to score at the
  day-120 cutoff. This narrows "scoring population" more than
  `design/high-level.md`'s abstract statement ("all players active in the
  trailing 30 days") - worth reconciling if this project's high-level doc
  is revisited, since a real deployment scoring on a rolling weekly cadence
  would not have this one-time cliff.

No duplicate rows or duplicate `player_id` values found in the train table.
No columns were found that contradict `design/high-level.md`'s named source
tables.

## Dashboard

`dashboard/eda.ipynb` built and executed with real cells (shape, nulls,
target balance, feature distributions - the same facts as above).
`dashboard/app.py` copied from the shared template, unedited. Streamlit
launched in the background; URL reported separately once confirmed
reachable.

## Change log

- 2026-09-20: Step 1 (data) completed. Feature cutoff set to day 120 (60-day
  horizon before the day-180 label), informed by the monkey-mode baseline's
  tautology finding for this project.
