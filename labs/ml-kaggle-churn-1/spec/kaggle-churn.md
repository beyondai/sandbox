prd-hash: 165cc22bc314aa28ae2ca3b41a822aa7214a204d
high-level-hash: a74d5f75e1961d862df155e0c0e6eefe6164b1c2

# Spec: kaggle-churn

## Problem Statement

Predict which customers will churn in the Kaggle Playground Series
synthetic telco-churn competition, to output a per-customer churn
probability for submission. Solo practice project (ML system design +
Kaggle skills), scored against the competition's own leaderboard.

## Solution

Binary classification: `P(Churn = Yes | customer features)`, output as a
probability in [0, 1]. Label is a static, already-observed outcome in
`train.csv` (no explicit forward-looking horizon — inherited from the
classic Telco Customer Churn framing this dataset derives from). Scoring
population/cadence: one-time batch scoring of all 254,655 `test.csv`
rows for competition submission, not a recurring live feed. Unit of
prediction: one row = one customer (`id`). `id` was tested and dropped — `mutual_info`
with `Churn` is 0.0002 (see `modeling/02-features.md`), confirming it
carries no real signal; excluded from the feature set. One model, one project folder. Architecture is offline
batch: `train.csv` -> clean/feature-pipeline -> train/val split -> model
training -> validation; `test.csv` -> same fitted pipeline -> trained
model -> `id,Churn` submission file -> Kaggle leaderboard (see ADR 0001
for why this batch path stands in for "online inference").

## Implementation Decisions

- Phasing: V0 baseline (RandomForestClassifier, fast defaults, done via
  monkey-mode, 0.9049 ROC-AUC) -> V1 first real model (resolve id-leakage
  and TotalCharges/tenure/MonthlyCharges redundancy, compare a GBM
  candidate under cross-validation, tune the decision threshold) -> V2
  stretch (light ensembling, calibration, real Kaggle submission run).
- Architecture's named source tables:
  `/Users/alex/dev/sandbox/data/playground-series-churn/train.csv`
  (labeled, training + internal eval) and
  `/Users/alex/dev/sandbox/data/playground-series-churn/test.csv`
  (unlabeled, Kaggle submission only — never used for training or eval).
- ADR 0001: the high-level design's "online inference" diagram is
  repurposed as the batch-scoring/submission path, since this project
  has no live serving surface.

## Testing Decisions

- Primary offline metric: ROC-AUC (matches Kaggle's own scoring exactly).
- Secondary/diagnostic: accuracy, precision/recall (or F1) at a chosen
  threshold, plus a basic calibration check, given the ~22.5%
  positive-class imbalance.
- Guardrail: none beyond avoiding leaderboard overfitting via excessive
  submission probing.
- Split rule: stratified random 80/20, `seed=42`, `test_share=0.20`,
  carved from the full `train.csv` (see `modeling/01-data.md` for
  reasoning).

## Out of Scope

Real-time/API serving; live A/B testing; an online feature store; heavy
ensembling/stacking; exhaustive hyperparameter search; a fairness/bias
audit across demographic slices; production monitoring. One-shot batch
Kaggle submission, not a deployed system.
