# 03 - Train (parallel candidates, Quick POC)

Grounding: `design/high-level.md`'s Phasing (V0 baseline, V1 "tuned
gradient-boosted trees"), `modeling/01-data.md`'s class balance (~50.35%
positive - no class-weighting needed), and `modeling/02-features.md`'s
Output table (`modeling/datasets/kkbox_train_features.csv`, train split
only - `dataset.test` was never opened here).

## Candidates chosen

Three genuinely different model families, not three flavors of the same
idea:

1. **Logistic Regression** - interpretable linear baseline, distinct
   model family from the tree-based baseline `monkey-mode/report.md`
   already validated (AUC 0.6727).
2. **Random Forest** - the same model class as that monkey-mode
   baseline (`n_estimators=200`, `max_depth=12`, held identical for
   comparability), now run on the full 112-column engineered feature
   table instead of 12 raw columns - a direct "does feature engineering
   help" test with the model class held fixed.
3. **HistGradientBoostingClassifier** (scikit-learn's native gradient
   boosting) - the "tuned gradient-boosted trees" model class
   `design/high-level.md`'s V1 phase and `monkey-mode/report.md` both
   point to. LightGBM/XGBoost were tried first but LightGBM failed to
   import on this machine (missing the system `libomp` library, not
   fixable with a quick Python-package install); `HistGradientBoostingClassifier`
   is a comparable substitute with zero extra system dependencies.

A neural network candidate was deliberately not tried - premature per
`design/high-level.md`'s V2/stretch phase and the embeddings-omission
reasoning in `ml-modeling-features/SKILL.md`; tree methods hadn't even
been tried at scale yet.

## First pass: implausible results, diagnosed as CV leakage

Initial 5-fold `StratifiedKFold` CV (each candidate trained by its own
subagent, in parallel):

| Model | CV AUC | Std |
|---|---|---|
| Logistic Regression | 0.7359 | 0.0014 |
| Random Forest | 0.7550 | 0.0023 |
| HistGradientBoosting | **0.9360** | 0.0014 |

HistGradientBoosting's 0.9360 was flagged immediately as implausible:
this is a well-studied public Kaggle task (WSDM/KKBOX 2018) whose top
public leaderboard scores sit around 0.737-0.748 AUC (checked directly
against the leaderboard - see caveat below), using much richer features
than available here, including raw listening logs this dataset doesn't
even expose. A same-scale model hitting 0.936 on held-out-looking data
has no legitimate explanation regardless of the exact leaderboard number
- this comparison was a sanity check on plausibility, not a claim that
our numbers are directly comparable to the leaderboard's (they aren't -
see the note in `04-evaluate.md`, "Not comparable to the public
leaderboard").

**Root cause**: `msno_repeat_rate_loo`, `song_repeat_rate_loo`, and
`artist_repeat_rate_loo` (see `02-features.md`) were computed *once*,
globally, before the 5-fold split - not re-derived per fold. Leave-one-out
only excludes a row's own label from its own group's statistic; it does
**not** exclude every other row from the same validation fold. So a
user's smoothed rate in a validation fold was partly built from *other
rows of that same user that also happened to land in that validation
fold* - a fold-crossing leak, not just the row-level leak the feature was
actually designed to prevent. `02-features.md` had flagged this as a
"mild, accepted simplification" - that assessment was wrong in degree:
HistGradientBoosting's iterative, fine-grained splitting could exploit it
far more aggressively than Random Forest's bagged/regularized trees or a
linear model could, which is exactly the differential pattern observed
(huge jump for HGB, much smaller for RF, smallest for the linear model).

## Fix

Two parts:

1. **Two real bugs found and fixed** in `modeling/build_features.py`
   while investigating (unrelated to the CV issue itself, but found
   along the way): `.astype(str)` doesn't stringify NaN on this pandas
   version, and pandas `groupby` silently drops NaN-keyed groups - both
   were producing unexpected NaN in `source_context_freq` and the
   `artist_*` columns. Fixed with explicit `.fillna("missing")` before
   grouping/concatenating, consistent with how every other categorical
   column here handles missingness. Full detail in `02-features.md`'s
   Change log. `kkbox_train_features.csv` was regenerated - only `bd`
   and `song_length_log` have any NaN now, both expected.
2. **Fold-safe re-run**: `modeling/train_candidates_fold_safe_cv.py`
   (new, run once, covering all three candidates together so they share
   identical folds). For each of 5 folds, `msno`/`song`/`artist`
   repeat-rates are recomputed from *that fold's training portion only*
   - leave-one-out within the fold's train rows for fitting, and a plain
   smoothed mean (via left-join, exactly the "Applying to the test
   split" methodology from `02-features.md`) applied to that fold's
   validation rows. Every other column in the feature table doesn't
   depend on the target at all (one-hot, value-frequency encodings, date/
   log transforms), so it carries no fold-crossing leakage risk and was
   reused as-is.

## Final comparison (fold-safe, trustworthy)

| Model | CV AUC | Std | vs. first pass |
|---|---|---|---|
| **Random Forest** | **0.7351** | 0.0020 | was 0.7550 (mildly inflated) |
| Logistic Regression | 0.7333 | 0.0015 | was 0.7359 (mildly inflated) |
| HistGradientBoosting | 0.6126 | 0.0037 | was 0.9360 (**massively** inflated) |

This confirms the diagnosis completely. Logistic Regression and Random
Forest barely moved - a linear model and a bagged/regularized tree
ensemble can't exploit fine-grained fold-crossing leakage much.
HistGradientBoosting collapsed from best to worst: its CV score was
almost entirely a leakage artifact, not genuine model quality.

**HistGradientBoosting's genuine underperformance** (0.6126, below even
the linear baseline) is likely a tuning issue, not evidence gradient
boosting is wrong for this problem - `max_iter=200` with default
`learning_rate` and no early stopping may simply not suit this feature
set out of the box. Not pursued further in this Quick POC pass; worth
revisiting (learning rate, max leaf nodes, early stopping) before ruling
out gradient boosting as `design/high-level.md`'s V1 model class.

## Winner: Random Forest

Wins on the primary metric (AUC, per `prd/kkbox-recommendation.md`'s
Metrics - Offline), narrowly ahead of Logistic Regression (0.7351 vs.
0.7333 - close, but consistent across all 5 folds, not a coin flip) and
clearly ahead of HistGradientBoosting once leakage is removed. Also still
clears the `monkey-mode/report.md` baseline (AUC 0.6727 on 12 raw
columns, same model class) by ~0.062 - confirming the feature engineering
in `02-features.md` genuinely helps, not just the leakage that inflated
the first-pass number.

### Winner's actual training code (run, not a template)

The model actually handed off to `ml-modeling-evaluate` - a single fit on
the full training table, no CV (a single full fit has no folds to
leak across, so the original `kkbox_train_features.csv` leave-one-out
columns are used directly and are correctly leakage-free here):

```python
"""Final fit of the winning Random Forest candidate on the full training
table - no CV here, just the deployable model. The CV-leakage issue found
during candidate comparison (see 03-train.md) only affects reusing a
pre-built feature table ACROSS folds; a single fit on the whole table has
no folds to cross-contaminate, so the original kkbox_train_features.csv
(post-bug-fix, see 02-features.md's Change log) is used as-is here.
"""

import time
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

FEAT_PATH = "modeling/datasets/kkbox_train_features.csv"
OUT_PATH = "modeling/train-candidates/random-forest/model.joblib"

t0 = time.time()
df = pd.read_csv(FEAT_PATH)
X = df.drop(columns=["row_id", "target"])
y = df["target"]

model = Pipeline([
    ("impute", SimpleImputer(strategy="median")),
    ("clf", RandomForestClassifier(
        n_estimators=200, max_depth=12, random_state=42, n_jobs=4
    )),
])
model.fit(X, y)
elapsed = time.time() - t0

joblib.dump(model, OUT_PATH)
print(f"fit on {len(df)} rows, {X.shape[1]} features in {elapsed:.1f}s")
print(f"model saved to {OUT_PATH}")
```

Real output: `fit on 480000 rows, 110 features in 43.2s` - model saved to
`modeling/train-candidates/random-forest/model.joblib`.

## Class imbalance

Not applicable: target is ~50.35% positive per `01-data.md`, close enough
to balanced that no class-weighting or resampling was used for any
candidate.

## Where the other candidates' code lives

Each candidate's own training script and (corrected) metrics are in
`modeling/train-candidates/<model>/` - `logistic-regression/`,
`random-forest/`, `hist-gradient-boosting/`. The fold-safe comparison
script that produced the trustworthy numbers above is
`modeling/train_candidates_fold_safe_cv.py`; its raw per-fold output is
`modeling/fold_safe_cv_results.json`.

## Logged experiments

`modeling/experiments.json`: `logistic_regression_v1`/`random_forest_v1`/
`hist_gradient_boosting_v1` (the original, leaky CV numbers - kept for
the record, not for decisions) and `logistic_regression_v2_fold_safe`/
`random_forest_v2_fold_safe`/`hist_gradient_boosting_v2_fold_safe` (the
corrected numbers this decision is based on).

## Change log

- 2026-09-21: initial multi-candidate comparison, leakage diagnosed and
  fixed, Random Forest selected as winner.
- 2026-09-21: tightened the public-leaderboard sanity-check number
  (0.71-0.74 -> 0.737-0.748, checked directly against the leaderboard)
  after the user asked whether this project's results are evaluated
  against the same dataset as that leaderboard - they aren't; see
  `04-evaluate.md`'s "Not comparable to the public leaderboard" note.
  This section's use of the leaderboard was always just a plausibility
  sanity check (0.936 is absurd on any reasonable reading), not a claim
  of direct comparability - now stated explicitly.
