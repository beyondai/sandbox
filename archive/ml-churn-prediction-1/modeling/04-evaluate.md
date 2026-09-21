# Evaluate: Churn Prediction

*Updated by `ml-modeling-autoresearch` round 3 — Logistic Regression, C=0.1, plus engineered `ticket_rate` feature. Full history in `modeling/autoresearch/rounds/`.*

## Metrics (test split)

Accuracy 0.850, Precision 0.600, Recall 0.750, **F1 = 0.6667**.

## Baseline comparison

Majority-class baseline: accuracy 0.800, precision/recall/F1 all 0.0. The model clears this comfortably on F1 (0.6667 vs. 0.0).

## Overfit check

Train F1 0.675 vs. test F1 0.667 — a 0.008 gap, the smallest yet across all three model versions (original 0.042, round 2 0.031, round 3 0.008). The added feature improved both fit and generalization together.

## Progression

| Version | Change | F1 |
|---|---|---|
| Original | Logistic Regression, default C=1.0 | 0.6296 |
| Round 2 | + tuned C=0.1 | 0.6415 |
| Round 3 | + engineered `ticket_rate` feature | **0.6667** |

## Verdict

Clears the bar: F1=0.6667 vs. baseline F1=0.0, real learnable signal. Improved twice by autoresearch (regularization tuning, then a feature grounded in the original coefficient analysis).

Done: matches `modeling/04-evaluate.json`.
