# Autoresearch Program

## Config
- primary_metric: auc_roc
- candidates_per_round: 2
- time_budget_minutes: 2
- patience: 5
- improvement_tolerance: 0.005
- round_ceiling: 50

## Guidance

Quick POC mode - single train/test split (modeling/datasets/
kkbox_{train,test}_features.csv), same tables 03-train.md/04-evaluate.md
used. Current best is Random Forest (n_estimators=200, max_depth=12),
AUC 0.7361.

Known context from this project's record, worth drawing hypotheses from:

- HistGradientBoostingClassifier underperformed badly in the original
  3-candidate comparison (fold-safe AUC 0.6126, below even the linear
  baseline) with untuned defaults (max_iter=200, default learning_rate,
  no early stopping) - modeling/03-train.md flagged this as likely a
  tuning issue, not evidence the model class is wrong, and it's the
  model class design/high-level.md's V1 phase actually names. A tuned
  HGB variant (lower learning_rate + more iterations, or early_stopping
  enabled) is a reasonable hypothesis to try.
- `gender` was flagged by monkey-mode/report.md as low-importance and
  40% null, kept in the current feature set "for now" per
  02-features.md with a note that ml-modeling-train should re-check it
  against real feature importances - never actually done. Worth trying
  as a drop.
- Random Forest itself was never tuned beyond monkey-mode's original
  n_estimators=200/max_depth=12 choice (kept for comparability, not
  because it was searched). More trees or a different max_depth is a
  reasonable hypothesis.

One focused hypothesis per candidate - not a kitchen sink of unrelated
changes.
