# Round 0001

2 candidates, current best going in: Random Forest, auc_roc 0.7361436524739464
(`modeling/autoresearch/best_metrics.json`).

## candidate-drop-gender

Random Forest (same hyperparameters), `gender_female`/`gender_male`/
`gender_missing` dropped from the feature set. auc_roc **0.7369243805392733**
(+0.000781 vs. best). Below `improvement_tolerance` (0.005 relative,
~0.00368 absolute needed) - **discarded**, not promoted, despite being
nominally higher. Real signal that `gender` carries little weight
(consistent with monkey-mode's original flag), but not a strong enough
improvement to act on by itself in this round.

## candidate-hgb-tuned

Tuned `HistGradientBoostingClassifier` (`learning_rate=0.05, max_iter=500,
early_stopping=True, n_iter_no_change=20, validation_fraction=0.1`).
auc_roc **0.618560** (-0.117583 vs. best) - worse than even the original
untuned HGB run (0.6126) by only a small margin. A deeper-tree sanity
variant tried by the same candidate (`max_leaf_nodes=63, max_depth=10`)
scored worse still (0.578), pointing away from "undertrained" as HGB's
problem and toward this feature set (heavy one-hot + leave-one-out
target-encoded columns) simply not suiting gradient boosting as well as
Random Forest here. **Discarded.**

## Outcome

Neither candidate cleared `improvement_tolerance`. Current best is
unchanged: Random Forest, auc_roc 0.7361436524739464. Non-improvement
streak: **1** (of `patience` 5).
