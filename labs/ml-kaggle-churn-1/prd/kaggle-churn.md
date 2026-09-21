# Kaggle Churn — Definition (Quick POC)

## Problem

Predict which customers will churn, from the Kaggle Playground Series
synthetic telco-churn dataset, to output a per-customer churn probability
for competition submission. This is a solo practice project (ML system
design + Kaggle skills), not tied to a real company initiative — the "pain
point" is the competition's own leaderboard objective, standing in for the
real-world one ("which customers to target for retention before they
leave").

## Requirements — scope

Must-have: train a binary classifier on `train.csv` (594,194 rows, 20
features), output calibrated churn probabilities for all 254,655
`test.csv` rows in the exact `id,Churn` submission format.

Out-of-scope for this POC:
- Real-time/API serving
- Live A/B testing
- An online feature store
- Heavy ensembling/stacking
- Exhaustive hyperparameter search
- A fairness/bias audit across demographic slices
- Production monitoring

This is a one-shot batch Kaggle submission, not a deployed system.

## Requirements — non-functional

No real latency/availability SLA — this is a Kaggle competition, not a
production service. "Load" is a one-time batch scoring pass over 254,655
test rows before the (self-imposed) deadline. The only real non-functional
constraint is iteration speed: training should complete in minutes on
local sandbox hardware, not hours, since this is a POC loop.

## Metrics — offline

Primary = ROC-AUC, computed on a held-out validation split from
`train.csv` — this matches Kaggle's own evaluation exactly (submissions
are scored on area under the ROC curve between predicted probability and
observed target), so validation score is directly comparable to
leaderboard score.

Secondary/diagnostic: accuracy and precision/recall (or F1) at a chosen
threshold, plus a basic calibration check, given the ~22.5% positive-class
imbalance (460,377 "No" / 133,817 "Yes" in `train.csv`).

## Metrics — online

Not applicable in the usual sense — there's no live system or real users.
The closest analog is the Kaggle public/private leaderboard ROC-AUC after
submission. No traditional guardrail metric, but the practical guardrail
is: don't overfit to the public leaderboard by over-submitting/probing.

## Team

Solo project — no stakeholders, collaborating teams, or blocking/blocked
dependencies. Data is already downloaded locally at
`/Users/alex/dev/sandbox/data/playground-series-churn`.

## Team — reuse

Reusable: the sandbox's shared `uv` venv/`pyproject.toml` (pandas, numpy,
scikit-learn, etc.), already used by other labs projects and by the
monkey-mode baseline that ran in this same project folder
(`monkey-mode/report.md` — RandomForestClassifier baseline, ROC-AUC
0.9049 on a held-out split).

Downstream consumers: none — the Kaggle submission file is the terminal
deliverable, nothing else consumes this system's output.
