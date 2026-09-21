# Modeling Step 4 — Evaluate (Quick POC)

No mode keyword in this request. Continuing Quick POC — reports the
metrics that actually distinguish "does this work" (baseline comparison,
overfit gap, imbalance-aware primary metric) and stops there, rather
than the full Regular-mode metric/diagnostic set.

Design docs changed? `prd/kaggle-churn.md` and `design/high-level.md`
hashes still match `spec/kaggle-churn.md`'s pinned hashes. Proceeding.

Scored on `01-data.json` -> `dataset.test`
(`modeling/datasets/churn_test.csv`, 118,839 rows) — read here for the
first time in this chain. `dataset.split.type` is `random` (not
`cutoff`): this is a stratified random hold-out, not a backtest at a
later cutoff, since the label has no time dimension (see
`design/high-level.md`'s ML framing).

The same pure row-wise feature-engineering function from
`modeling/engineer_features.py` (`add_engineered_features`) was applied
to this split before scoring, and `id` was dropped, matching exactly
what the winning pipeline was trained on — no new leakage risk, since
that function uses no train-fitted statistic (see `02-features.md`).

## Results (test split, 118,839 rows, `hist_gradient_boosting`)

| Metric | Value |
|---|---|
| **AUC-ROC (primary)** | **0.9155** |
| F1 | 0.684 |
| Precision | 0.5595 |
| Recall | 0.8798 |
| Accuracy | 0.8169 |

## Baseline comparison

| | Model | Naive baseline |
|---|---|---|
| AUC-ROC | 0.9155 | 0.5 (non-informative classifier) |
| Accuracy | 0.8169 | 0.7748 (always predict majority class `No`) |
| F1 | 0.684 | 0.0 (majority-class predictor never predicts the minority class) |

The model clears every naive baseline by a wide margin — accuracy alone
would understate this, since the 77.5%/22.5% class split means a
do-nothing majority-class predictor already scores 77.48% accuracy; the
real signal is in AUC-ROC and F1, where the baseline is 0.5 and 0.0
respectively.

## Overfit check

| | Train (fit table) | Test (held-out) | Gap |
|---|---|---|---|
| AUC-ROC | 0.9171 | 0.9155 | **0.0016** |
| F1 | 0.6862 | 0.6840 | 0.0022 |

Gap is negligible on both metrics — this model is not overfitting the
training table. The held-out test AUC-ROC (0.9155) also lands almost
exactly on top of `03-train.md`'s 3-fold CV estimate (0.9148, std
0.0007) for the same candidate, confirming the CV ranking used to pick
the winner was trustworthy, not optimistic.

## Class imbalance note

Target is 77.5%/22.5% (No/Yes) — imbalanced enough that accuracy alone
would mislead, so AUC-ROC leads as PRD's stated primary metric, with F1
as the imbalance-aware secondary check. At the default 0.5 threshold,
`class_weight="balanced"` (set in `ml-modeling-train`) pushed the
model toward much higher recall on churners than monkey-mode's
untuned V0 baseline (87.98% vs. 61.7%), at the cost of lower precision
(55.95% vs. 68.9%). This is the exact threshold/precision-recall
tradeoff `design/high-level.md`'s Phasing V1 flagged as worth
addressing — not resolved further here (threshold tuning by target
precision/recall is a natural `ml-modeling-autoresearch` follow-up, not
required by the PRD's stated metrics, which don't set a precision or
recall floor).

## Comparison to prior runs

Logged via `experiment_tracker.py compare --ids 1 2 3` (full comparison
table in `modeling/experiments.json`):

- V0 baseline (`monkey-mode/report.md`, untuned RandomForest, single
  80/20 split, no engineered features): **0.9049** held-out AUC-ROC.
- V1 candidates (this chain, 3-fold CV, engineered features, class
  weighting): `random_forest` 0.9121, `hist_gradient_boosting`
  **0.9148** (CV mean) -> **0.9155** on the actual held-out test split.

**Verdict: this model is good enough to call V1 done.** It clears
monkey-mode's self-inferred POC success bar (0.85-0.88 AUC-ROC) with
room to spare, and it beats the V0 baseline by +0.0106 AUC-ROC
(0.9049 -> 0.9155) — the explicit goal `design/high-level.md`'s Phasing
V1 set for this step. Overfitting is negligible (0.0016 gap). The one
open, explicitly-deferred question is the precision/recall tradeoff at
the decision threshold, which is a V2/autoresearch-scope refinement, not
a blocker on the PRD's own stated metrics.

## Spec self-staleness

`spec/kaggle-churn.md`'s Testing Decisions section already stated the
primary/secondary metrics and guardrail as decisions, not placeholders —
this step's results don't contradict anything recorded there. No spec
edit needed.
