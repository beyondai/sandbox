# Riot Churn - Step 2: Features

Mode: Quick POC - obviously useful transforms applied and justified against
`01-data.md`'s profile and risk flags, no exhaustive search.

Design docs unchanged since `spec/riot-churn.md` was synthesized (hash
check passed silently).

## Input

`01-data.json` -> `dataset.train` (`datasets/churn_train.csv`). Test
(`datasets/churn_test.csv`) was never opened while choosing these
transforms - see "Output table" below for why applying the same code to it
afterward is still safe.

## Transforms applied

Script: `modeling/engineer_features.py`.

- **`region` -> one-hot with an explicit `unknown` category**: 29.5% null
  in the train profile, matching the raw source's 29.3% - a real segment,
  not a bug. Filled to the literal string `"unknown"` before one-hot so the
  model can weigh "region not captured" as its own signal, rather than
  imputing a guessed region or dropping the column.
- **`platform`, `acquisition_source` -> one-hot (drop-first)**: low
  cardinality (2 and 3 values), no null rate, straightforward.
- **`has_purchased` (new, binary)**: `purchase_count > 0`. Justified by
  01-data.md's flag that only 8.6% of scored players purchased anything
  pre-cutoff - makes that sparsity an explicit, low-noise signal.
- **`total_spend_log`, `purchase_count_log` (replace raw)**: `log1p`.
  Justified by skew 8.18 / 7.00 in 01-data.md - raw values would let a
  handful of large spenders dominate a linear model.
- **`total_party_games_log` (replace raw)**: `log1p`. Justified by skew
  1.83.
- **`signup_day` dropped**: deterministic linear transform of
  `tenure_at_scoring` (`tenure = 120 - signup_day`, from
  `build_dataset.py`) - pure duplicated information. Confirmed by
  `feature_selector.py` scoring the two almost identically (0.40 vs 0.27)
  before this was dropped.

## Left unchanged (and why)

- `active_days`, `total_games`, `total_wins`, `total_minutes`,
  `days_since_last_active`, `activity_trend`, `win_rate`,
  `tenure_at_scoring`, `days_since_last_purchase`, `distinct_item_types`:
  skew is mild (<=0.83) or the domain is already tiny
  (`distinct_item_types` is 0-3) - a log transform would add complexity
  without an obviously-useful payoff for a Quick POC baseline. Scaling
  (e.g. standardization for logistic regression) is deferred to the train
  step's pipeline, not done here, so this table stays scale-free and reusable
  regardless of which model class the train step picks.
- No time-based/cyclical features: no raw timestamp column exists in this
  table - `day` was already consumed by the aggregation in
  `build_dataset.py`.
- No target/frequency encoding: no high-cardinality categorical exists here
  (`region` tops out at 4 known values plus `unknown`).

## Selection - `feature_selector.py`

Run against `datasets/churn_train_features.csv`, target `label`:

```
Rank   Feature                     Score    Type
1      days_since_last_active      0.628    numeric
2      active_days                 0.527    numeric
3      total_wins                  0.525    numeric
4      total_games                 0.525    numeric
5      total_minutes               0.524    numeric
6      total_party_games_log       0.524    numeric
7      activity_trend              0.508    numeric
8      purchase_count_log          0.390    numeric
9      total_spend_log             0.389    numeric
10     distinct_item_types         0.388    numeric
11     has_purchased                0.386    numeric
12     days_since_last_purchase    0.306    numeric
13     player_id                   0.273    numeric
14     tenure_at_scoring           0.272    numeric
15-22  categorical dummies         0.26-0.26
23     win_rate                    0.257    numeric
```

`days_since_last_active` is the strongest single signal by a clear margin
(0.628) even with the feature cutoff moved to day 120 - this confirms the
horizon change in step 1 (day-120 features / day-180 label) produced a real
predictive signal rather than the same-day tautology the monkey-mode
baseline hit, since players are being scored 60 days before the labeled
outcome, not on the day of it. `player_id` scores low (0.273) as expected
for an identifier and is excluded from the feature matrix (kept in the
table only for row bookkeeping). Categorical dummies and `win_rate` rank
lowest - kept anyway for a Quick POC baseline (not dropped) since none
scored as noise (null/constant), just weaker signal; a later pass could
revisit dropping the weakest region/platform dummies if the train step's
model shows they add nothing.

Not dropped despite some inter-correlation: `active_days`, `total_games`,
`total_wins`, and `total_minutes` are all "volume of play" signals and
likely correlated with each other. Left as separate features for this POC
(a tree ensemble is not hurt by this, and it was out of scope to verify a
logistic-regression-specific multicollinearity check for a Quick POC) -
worth a VIF/correlation-matrix pass in V1 if this becomes a
logistic-regression production candidate.

## Output table

`modeling/datasets/churn_train_features.csv` (7,224 rows x 23 columns) and
`modeling/datasets/churn_test_features.csv` (1,805 rows x 23 columns),
written by `modeling/engineer_features.py`. Final feature matrix for the
train step is every column except `player_id` (id, not a feature) and
`label` (target) - 21 features: `tenure_at_scoring`, `active_days`,
`total_games`, `total_wins`, `total_minutes`, `win_rate`,
`days_since_last_active`, `activity_trend`, `distinct_item_types`,
`days_since_last_purchase`, `has_purchased`, `total_spend_log`,
`purchase_count_log`, `total_party_games_log`, `region_EUW`, `region_KR`,
`region_LATAM`, `region_unknown`, `platform_pc`,
`acquisition_source_organic`, `acquisition_source_paid_ads`.

Test was transformed with the exact same code path as train
(`engineer()` in `engineer_features.py`), not a separately-derived version -
every transform used here is a fixed rule (log1p, a fixed set of one-hot
categories, a threshold at 0) with nothing fit from data, so this carries
no leakage despite producing both tables from one function.

## Change log

- 2026-09-20: Step 2 (features) completed.
