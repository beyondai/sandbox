---
name: ml-modeling-evaluate
description: Use to evaluate a trained model rigorously — classification/regression metrics, baseline comparison, overfitting check. Step 4 (final) of the ml-modeling-* chain (data → features → train → evaluate). Trigger on "evaluate this model," "compare to baseline," "is this overfitting," or continuing modeling work in an existing ml-<topic>-<n>/ project.
---

# Evaluate

Reads `<project-folder>/design/deep-dive.md`'s Training section (required) and `modeling/03-train.md` — written by either `ml-modeling-train` or `ml-modeling-multiagent`, doesn't matter which. Writes `<project-folder>/modeling/04-evaluate.md`. This is the last step in the chain — see `ml-modeling` router for what comes after.

Mode: Regular reports the full metric set below and checks overfit explicitly. Quick POC reports the metrics that actually distinguish "does this work" and stops there — see `ml-modeling` router for the keyword rule.

## Classification

```python
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

def evaluate_classifier(y_true, y_pred, y_proba=None):
    m = {"accuracy": accuracy_score(y_true, y_pred), "precision": precision_score(y_true, y_pred),
         "recall": recall_score(y_true, y_pred), "f1": f1_score(y_true, y_pred)}
    if y_proba is not None:
        m["auc_roc"] = roc_auc_score(y_true, y_proba)
    return m
```

## Regression

```python
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

def evaluate_regressor(y_true, y_pred):
    return {"mae": mean_absolute_error(y_true, y_pred),
            "rmse": np.sqrt(mean_squared_error(y_true, y_pred)), "r2": r2_score(y_true, y_pred)}
```

## Required checks

- **Baseline comparison**: report the model's metrics against a naive baseline (majority class, or mean prediction), not in isolation — a metric with no baseline is a number, not evidence.
- **Overfit check**: train-vs-test gap on the primary metric. A large gap means the reported test number isn't trustworthy even if it looks good.
- **Class imbalance**: if the target is imbalanced, accuracy alone is misleading — lead with F1/precision-recall/AUC-ROC instead.
- **Log the comparison**: `python3 ../ml-modeling/scripts/experiment_tracker.py compare --ids <ids>` against prior runs (especially useful if `ml-modeling-multiagent` produced multiple candidates).

## A/B testing an already-shipped model

Out of the main chain — only relevant once a model is live and being compared against production traffic. See [references/ab-testing.md](references/ab-testing.md) for sample-size calculation and result analysis, and `../ml-modeling/scripts/hypothesis_tester.py` to actually run the test.

Done when metrics are reported against a real baseline (not standalone), the overfit check has an actual train/test gap number, and `04-evaluate.md` states plainly whether this model is good enough — not just what the numbers are.
