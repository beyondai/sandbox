---
name: ml-modeling-evaluate
description: >-
  Use to evaluate a trained model rigorously - classification/regression
  metrics, baseline comparison, overfitting check. Also writes the project
  dashboard's Final Results section. Step 4 of the ml-modeling-* chain
  (data → features → train → evaluate → serve). Trigger on "evaluate this model,"
  "compare to baseline," "is this overfitting," or continuing modeling work in
  an existing ML project folder.
---

# Evaluate

Contents: Classification | Regression | Required checks | A/B test of a shipped
model | Dashboard results | Check | After this step

- **Reads:** the offline metrics in `<project-folder>/prd/<topic>.md`
  (primary, secondary, guardrails: they define "good enough") and
  `modeling/03-train.md` (from `ml-modeling-train` or
  `ml-modeling-multiagent`). If the PRD has no primary metric or no
  numeric bar, say so and state the bar you use as an assumption.
- **Loads:** `modeling/model.joblib` and `transform()` from
  `modeling/features.py`. Do not refit on test (see "Handoff" in
  `../ml-modeling/SKILL.md`).
- **Scores on:** `01-data.json` -> `dataset.test`. The train number for the
  overfit gap comes from the table that the model was fit on.
- **Writes:** `modeling/04-evaluate.md`, `modeling/04-evaluate.json`, and
  the per-row scores in `modeling/test_scores.csv`.
- **Rules:** `../ml-system-design/SKILL.md`, "Project folder", "Output
  docs", "Check the output", "Skill improvement log".
- **Mode:** Regular reports the full metric set and the overfit check.
  Quick POC reports the metrics that show "does this work".

Steps:
1. Run "Design docs changed?" in `../ml-modeling/SKILL.md`.
2. Score the model and the baseline on the test split, once. Save
   `test_scores.csv`.
3. Do the required checks, including the noise of the lift.
4. Write `04-evaluate.md` and `04-evaluate.json`.
5. Confirm that the dashboard responds (not in monkey-mode).
6. Check.

If `dataset.split.type` is `cutoff`, say in `04-evaluate.md` that this is
a backtest at a later cutoff, not a random hold-out.

## Classification

```python
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score)

def evaluate_classifier(y_true, y_pred, y_proba=None):
    m = {"accuracy": accuracy_score(y_true, y_pred),
         "precision": precision_score(y_true, y_pred),
         "recall": recall_score(y_true, y_pred),
         "f1": f1_score(y_true, y_pred)}
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
            "rmse": np.sqrt(mean_squared_error(y_true, y_pred)),
            "r2": r2_score(y_true, y_pred)}
```

## Required checks

- **Baseline.** Report the model against a baseline on the same split. Use
  the PRD's recommended baseline (Definition, "Baseline"). If it is not
  built and it is a simple rule (for example a recency rule or global
  popularity), score it now: a model that only beats the floor can lose
  to a one-line rule. Also report the floor (majority class, mean
  prediction). If the recommended baseline cannot be built now, say so.
- **Noise.** Give a 95% interval for the lift over the baseline: a paired
  bootstrap on `test_scores.csv` (resample rows, recompute both metrics).
  `hypothesis_tester.py` covers means and proportions, not AUC or top-k.
- **Overfit.** Give the train-vs-test gap on the primary metric. A large
  gap makes the test number unreliable.
- **Class imbalance.** For an imbalanced target, lead with F1,
  precision-recall, or AUC-ROC, not accuracy.
- **Log the comparison.** Put `--log-file` before the subcommand:

  ```
  python3 .agents/skills/personal/ml-modeling/scripts/experiment_tracker.py \
    --log-file <project-folder>/modeling/experiments.json compare --ids <ids>
  ```

## A/B test of a shipped model

Only for a model that is live. Sample size and analysis:
[references/ab-testing.md](references/ab-testing.md). Run the test with
`python3 .agents/skills/personal/ml-modeling/scripts/hypothesis_tester.py`.

## Dashboard results

Regular and Quick POC only. Write the results to `04-evaluate.json`. The
dashboard reads the JSON, not the `.md`.

```json
{
  "primary_metric": "f1",
  "metrics": {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0},
  "baseline_metrics": {},
  "overfit_gap": {"train": 0.0, "test": 0.0},
  "success_bar": "<string>",
  "verdict": "<one sentence: clears or misses the bar, and why>",
  "verdict_status": "pass | partial | fail"
}
```

Then run:

```
bash .agents/skills/personal/ml-modeling-data/scripts/launch_dashboard.sh <project-folder>
```

It reuses the project's running dashboard, or starts it again on the
port in `dashboard/.port`. Do not check the bare port `:8501`: it can be
another project's dashboard. Do not edit `dashboard/app.py`.

## Check

Do "Check the output" in `../ml-system-design/SKILL.md`. Intent questions:
1. Is the model compared with the recommended baseline (or a simple rule)
   on the same test split, not only with the floor?
2. Does the 95% interval of the lift exclude zero? If not, does the
   verdict say "inside the noise"?
3. Does the overfit check give a real train/test gap number?
4. Does `04-evaluate.md` say plainly if the model is good enough for the
   PRD bar, not only the numbers? Does `04-evaluate.json` match it?

Done when the 4 answers are yes, `check_doc.py` prints `OK`, and
`launch_dashboard.sh` prints `RUNNING` or `STARTED`.

## After this step

- Next: `ml-modeling-serve` (step 5) measures how this model serves.
- `ml-modeling-autoresearch` (user-run only) tries to beat this result:
  one round, until plateau, or for a duration. See
  `../ml-modeling-autoresearch/SKILL.md`. After a promotion, run step 5
  again.
