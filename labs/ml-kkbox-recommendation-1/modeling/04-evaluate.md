# 04 - Evaluate (Quick POC)

Grounding: `prd/kkbox-recommendation.md`'s Metrics - Offline (AUC, no
separate proxy metric needed) and `modeling/03-train.md` (winner: Random
Forest, `n_estimators=200`, `max_depth=12`, fit on the full
`kkbox_train_features.csv`, saved to
`modeling/train-candidates/random-forest/model.joblib`).

Scored on `01-data.json` -> `dataset.test` (`modeling/datasets/
kkbox_test.csv`, 120,000 rows) - never opened by any earlier step.

## Building the test features

`dataset.test` had no engineered features yet - `02-features.md`'s
"Applying to the test split" section specified exactly how to build them,
executed here as `modeling/build_test_features.py`. Found and fixed one
more real bug while doing this: `genre_primary_top.csv` stores genre ids
as bare digits (`465`), which pandas reads back as `int64` - but
`genre_primary` in the test script is a string column (`"465"`). Their
`.isin()` comparison silently never matched anything, so **every single
test row fell into the `genre_primary_other` bucket** before the fix.
Fixed by forcing `dtype=str` on that one read. After the fix, only one
column needed zero-filling (`source_screen_name_Concert` - present in
train, zero occurrences in test, which is legitimate, not a bug).

`modeling/datasets/kkbox_test_features.csv` (120,000 rows, 110 feature
columns, aligned exactly to `kkbox_train_features.csv`'s column set).

## Metrics

| Metric | Value |
|---|---|
| **AUC-ROC** (primary) | **0.7361** |
| Accuracy | 0.6730 |
| Precision | 0.6753 |
| Recall | 0.6751 |
| F1 | 0.6752 |

Class imbalance isn't a concern here (target is ~50.35% positive per
`01-data.md`), so accuracy isn't misleading on its own the way it would be
for a skewed target - AUC is still the metric that matters per the PRD,
and precision/recall/F1 are reported as the fuller picture, not because
imbalance forces them to lead.

## Baseline comparison

- **Majority-class baseline**: 0.5035 accuracy (= the test set's own
  positive rate - a majority-class predictor gets this "for free").
  Random Forest's 0.6730 accuracy clears it by +0.170.
- **Random baseline**: AUC 0.5. Random Forest's 0.7361 clears it by
  +0.236.
- **monkey-mode baseline, true same-test-set comparison**: `monkey-mode/
  report.md` originally reported AUC 0.6727 on its own independently-
  sampled 80/20 split - not this project's exact `kkbox_test.csv`, and it
  saved no trained model to re-score (`monkey-mode/baseline.py` has no
  `joblib.dump`). To get a rigorous comparison, `modeling/
  rerun_monkey_mode_on_test.py` retrains monkey-mode's *exact* approach
  (same 12 raw columns - `song_length`, `bd`, `registration_init_time`,
  `expiration_date`, `source_system_tab`, `source_screen_name`,
  `source_type`, `city`, `gender`, `registered_via`, `language`,
  `isrc_country`; same median/most-frequent imputation + one-hot;
  same `RandomForestClassifier(n_estimators=200, max_depth=12,
  random_state=42)`) on this project's actual `kkbox_train.csv` and
  scores it on this project's actual `kkbox_test.csv` - the identical
  120,000 test rows the winning model was evaluated on above. Result:
  **AUC 0.6746** (accuracy 0.6288, precision 0.6397, recall 0.6016, F1
  0.6200, train AUC 0.6848). This project's Random Forest - same model
  class, 110 engineered columns instead of 12 raw ones - scores
  **0.7361, beating it by +0.0615 AUC** on the exact same held-out rows.
  Reassuringly, 0.6746 is very close to monkey-mode's originally-reported
  0.6727 (+0.0019) - confirming the earlier approximate comparison (before
  this rigorous re-run) was already a reasonable signal, not an artifact
  of comparing different splits. This is the comparison that matters most
  for judging whether the feature-engineering and model-selection work in
  this project was worth it: it was, and now on solid evidence rather than
  an approximation.

## Overfit check

Train (the table the model was fit on): AUC 0.7691. Test: AUC 0.7361.
Gap: **0.0330** - modest, not alarming for `max_depth=12` trees. Worth
noting this gap is close to the CV-vs-test consistency check below, which
is itself a form of validation that the model generalizes reasonably.

## CV estimate vs. real test result - a consistency check on the leakage fix

`modeling/03-train.md` diagnosed and fixed a CV-fold leakage bug during
model selection; the fold-safe CV estimate for Random Forest was
**0.7351**. The real, independent test-set AUC here is **0.7361** - a
0.001 difference, well within noise. This is strong evidence the
fold-safe CV fix in `03-train.md` was correct: if it had undercorrected
(still somewhat leaky) or overcorrected (too conservative), this test
number would likely have diverged further from 0.7351 in one direction.
It didn't - the corrected CV estimate and the true held-out result agree
closely.

## Verdict

**Clears the bar.** Test AUC 0.7361 exceeds the 0.65 bar established with
the user for this exercise (via `monkey-mode/report.md`'s success-bar
question; the PRD names AUC as the metric but sets no separate numeric
threshold of its own), and beats a true same-test-set re-run of
monkey-mode's exact approach by +0.0615 AUC. The overfit gap (0.033) is
modest. This model is good enough to call the Quick POC's V0 phase
(`design/high-level.md`) complete.

## Not comparable to the public leaderboard

The user asked directly whether this project's numbers are evaluated
against the same dataset as the real WSDM/KKBOX 2018 Kaggle leaderboard
(top public scores sit around 0.737-0.748 AUC, per the leaderboard itself
- shown to this session directly). **They are not, and can't be:**

- Kaggle's actual `test.csv` is unlabeled - it's the real competition
  submission set. Scoring against it means submitting to Kaggle's
  servers, which is out of scope for this practice project. `01-data.md`
  flagged this from the start: `test.csv` "was not used."
- This project's "test set" (`modeling/datasets/kkbox_test.csv`) is
  self-made: an 80/20 split of a 600,000-row sample `build_dataset.py`
  drew from the ~7.4M-row `train.csv` - not Kaggle's real held-out rows.
- Leaderboard entries typically trained on the full `train.csv` plus
  `user_logs.csv` (raw per-day listening history) - a table this WSDM
  release doesn't even include (see `01-data.md`'s Dataset section). This
  project's features are necessarily built from a smaller, less complete
  picture.

The leaderboard number was used earlier in `03-train.md` purely as a
plausibility sanity check (a model scoring 0.936 is implausible on any
reasonable reading of this task, regardless of the exact leaderboard
figure) - not as a claim that this project's AUC 0.7361 is directly
comparable to those scores. The comparisons that *are* valid here are the
same-population ones: against the majority-class/random baselines and
against monkey-mode's exact approach re-run on this project's own test
set, both above.

## Logged experiments

`modeling/experiments.json`: experiment #7 (`random_forest_final_test_eval`)
and #8 (`monkey_mode_baseline_rerun_on_real_test`). Comparison against the
CV runs (`experiment_tracker.py compare --ids 2 5 7 8`): the leaky CV (#2,
0.7550), fold-safe CV (#5, 0.7351), this project's real test result (#7,
0.7361), and monkey-mode's exact approach re-run on the same test rows
(#8, 0.6746) are all in the record side by side - the consistency between
#5 and #7 is the strongest evidence the leakage fix worked, and #8 is the
rigorous version of the baseline comparison.

## Dashboard

Confirmed reachable at the project's port (`curl -sf http://localhost:$(cat
dashboard/.port)`) - no relaunch needed. `04-evaluate.json` is in place
for its Final Results section.

## Change log

- 2026-09-21: initial evaluation against the held-out test split.
- 2026-09-21: added "Not comparable to the public leaderboard" after the
  user asked directly whether this project's numbers are evaluated
  against the same dataset as the real Kaggle leaderboard - they aren't.
- 2026-09-21: replaced the approximate monkey-mode comparison with a
  rigorous same-test-set re-run (`modeling/rerun_monkey_mode_on_test.py`)
  - AUC 0.6746 vs. the originally-reported 0.6727 (very close, validating
    the earlier approximation). Updated the baseline comparison, verdict,
    and `04-evaluate.json`'s `baseline_metrics.auc_roc` accordingly.
