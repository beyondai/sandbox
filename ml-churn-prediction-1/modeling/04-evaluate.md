# Evaluate: Churn Prediction

## Metrics (test split)

Accuracy 0.833, Precision 0.567, Recall 0.708, **F1 = 0.630**.

## Baseline comparison

Majority-class baseline: accuracy 0.800, precision/recall/F1 all 0.0 (never predicts the minority churn class). The model clears this comfortably on F1 (0.630 vs. 0.0) — real learnable signal, not baseline-matching noise.

## Overfit check

Train F1 0.672 vs. test F1 0.630 — a 0.042 gap, small enough not to be a concern.

## Verdict

Clears the bar: F1=0.6296 vs. baseline F1=0.0, real learnable signal.

Done: matches `modeling/04-evaluate.json`.
