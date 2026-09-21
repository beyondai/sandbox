# Riot Churn - Step 3: Train

Mode: Quick POC. Design docs unchanged since `spec/riot-churn.md` was
synthesized (hash check passed silently).

## Candidates and why these two

`design/high-level.md`'s Phasing names V0 as "baseline - logistic
regression or a single small tree ensemble." That explicitly overrides
Quick POC's default jump straight to the XGBoost/LightGBM workhorse row -
this project's own phasing says otherwise, so both named baseline
candidates were trained and compared instead of picking one by default.
This also matches the algorithm-selection matrix's "Small data (<10K rows)"
row (9,029 rows before the train/test split): start with Random Forest,
only upgrade to XGBoost if accuracy is insufficient.

Class imbalance: train positive rate is 66.6% (2,414 stayed / 4,810 left,
per `01-data.md`) - moderate, not severe. Handled with `class_weight`:
`"balanced"` on both candidates rather than resampling, per this step's
"weights first" default.

## Cross-validation

5-fold stratified CV on `modeling/datasets/churn_train_features.csv` only
(the "Output table" from `02-features.md`) - `churn_test_features.csv` was
never read in this step, per this skill's scope. Scored on F1 and
ROC-AUC (both trees-back to the PRD's offline metrics).

```
model.py: 5-fold StratifiedKFold(shuffle=True, random_state=42)
logistic_regression: Pipeline(StandardScaler -> LogisticRegression(
    class_weight="balanced", max_iter=2000, random_state=42))
random_forest: RandomForestClassifier(n_estimators=300, max_depth=8,
    class_weight="balanced", random_state=42, n_jobs=-1)
```

| Candidate | CV F1 (mean +/- std) | CV ROC-AUC (mean +/- std) |
|---|---|---|
| logistic_regression | 0.8207 +/- 0.0073 | 0.8827 +/- 0.0066 |
| random_forest | 0.8280 +/- 0.0082 | 0.8836 +/- 0.0051 |

## Chosen candidate: `random_forest`

It wins on both metrics, though narrowly (F1 +0.0073, ROC-AUC +0.0009 -
within a stddev of each other on ROC-AUC). Chosen over logistic regression
because: (1) it wins on the PRD's primary paired metrics, even if
narrowly; (2) it needs no scaling assumption for the mixed-scale feature
set built in step 2 (e.g. `total_minutes` in the thousands next to
`win_rate` in [0,1]); (3) it gives feature importances for free, which
directly explains the horizon-fix finding from step 1 (below) - logistic
regression's coefficients would need separate standardized-coefficient
work to give the same read. Logistic regression remains the fallback if a
future step needs a stakeholder-facing, coefficient-interpretable model
(per the algorithm-selection matrix's "interpretability required" row).

Sanity check on the horizon fix from step 1: the winning model's
feature-importance ranking is **not** dominated by a single tautological
recency feature the way the monkey-mode baseline's was (that one hit
ROC-AUC 0.99 with ~64% of importance in one recency feature, because it
scored on the same day as the label). Here, `days_since_last_active` is
still the top feature but only 32.7% of importance, with real weight
spread across `total_party_games_log` (14.5%), `activity_trend` (10.5%),
`total_minutes` (9.3%), and `active_days` (8.3%) - consistent with a
genuinely 60-days-ahead prediction task rather than a same-day tautology.

Top-10 feature importances (random_forest, fit on the full train table):

```
days_since_last_active     0.3271
total_party_games_log      0.1451
activity_trend              0.1046
total_minutes               0.0928
active_days                 0.0832
total_games                 0.0610
total_wins                  0.0535
days_since_last_purchase    0.0436
tenure_at_scoring            0.0380
win_rate                     0.0248
```

## Artifacts

- `modeling/train.py` - the actual training/comparison code that ran.
- `modeling/model.pkl` - the fitted winner (`random_forest`), pickled with
  its feature list, for the evaluate step to load.
- `modeling/cv_results.json`, `modeling/feature_importances.json` - raw
  numbers behind the tables above.
- Logged to `modeling/experiments.json` via `experiment_tracker.py`:
  `logistic_regression_v0` (CV F1 0.8207, CV ROC-AUC 0.8827) and
  `random_forest_v0` (CV F1 0.8280, CV ROC-AUC 0.8836).

## Change log

- 2026-09-20: Step 3 (train) completed. Winner: random_forest.
