# Riot Churn - Step 4: Evaluate

Mode: Quick POC. Design docs unchanged since `spec/riot-churn.md` was
synthesized (hash check passed silently).

Scored on `01-data.json` -> `dataset.test`
(`datasets/churn_test_features.csv`, 1,805 rows), `dataset.split.type` is
`random` (not `cutoff`) - this is a random stratified hold-out of players,
not a backtest at a later date; see `01-data.md` for why a temporal split
was not possible with this single-snapshot dataset.

## Metrics (test)

| Metric | Model (test) | Model (train) | Majority-class baseline |
|---|---|---|---|
| F1 | 0.8270 | 0.8623 | 0.7995 |
| ROC-AUC | 0.8748 | 0.9300 | 0.5000 |
| Precision | 0.9222 | 0.9583 | 0.6659 |
| Recall | 0.7496 | 0.7838 | 1.0000 |
| Accuracy | 0.7911 | 0.8333 | 0.6659 |
| Precision@top-20% risk | 0.9972 | - | - |

**Baseline comparison**: the majority-class baseline (always predict
"left," the 66.6% class) already scores F1 0.7995 - a known quirk of F1
under this much class imbalance, not a sign the model barely helps. The
metric that actually shows the model works is ROC-AUC: 0.8748 vs. 0.5
chance, a large, real gap. Precision@top-20%-risk (0.9972) is the most
operationally meaningful number for this project's actual use case
(campaign targeting can only act on a limited list): among the 361
highest-risk test players by predicted probability, 99.7% truly left.

**Overfit check**: F1 gap (train - test) = 0.0353; ROC-AUC gap = 0.0552.
Modest, expected for a depth-8 Random Forest on ~7,200 rows - not the
large gap that would make the test number untrustworthy.

**Class imbalance**: test positive rate is 66.6% (left), matching train
(`01-data.md`). Handled with `class_weight="balanced"` at train time (step
3); led with F1 and ROC-AUC together here rather than accuracy, per the
PRD's Metrics - offline section.

## Success bar and verdict

Bar (reused from this project's monkey-mode baseline's citation search
rather than a fresh lookup, since it is the same population and problem -
`monkey-mode/report.md`): **F1 ~0.65-0.78, ROC-AUC ~0.85-0.96**, from Khan
2020 (arXiv:2006.15735, WoW subscriber churn, 6-months-ahead, ~96%
ROC-AUC - close population match: an existing player base, not new
installs) and Mustac et al. 2022 (MDPI Applied Sciences 12(6):2795, F1
0.78 - explicitly a new-install population there, kept only as the best
available F1 reference, not treated as an equivalent-population number).

**Verdict**: clears the bar. Test F1 0.827 and ROC-AUC 0.875 both land
inside the cited soft-target ranges, with a small train/test gap - a real,
generalizing signal, not an overfit or tautological one (see `03-train.md`
for why the day-120/day-180 horizon fix specifically rules out the
tautology the monkey-mode baseline hit). Precision@20% (0.997) suggests
this v0 model is already good enough to drive a real "top-risk-players"
list for the existing comeback-campaign targeting mechanism named in
`design/high-level.md`.

## Logged comparison

`modeling/experiments.json`, via `experiment_tracker.py`:

```
#1 logistic_regression_v0    cv_f1_mean=0.8207  cv_roc_auc_mean=0.8827
#2 random_forest_v0          cv_f1_mean=0.8280  cv_roc_auc_mean=0.8836  (best CV)
#3 random_forest_v0_test_eval  f1=0.8270  roc_auc=0.8748
                                precision_at_20pct=0.9972  (best on all reported)
                                baseline_f1=0.7995  baseline_roc_auc=0.5
```

## Dashboard

`04-evaluate.json` written for the dashboard's Final Results tab. Confirmed
reachable: `curl -sf http://localhost:8502` succeeded (port recorded in
`dashboard/.port`).

## Change log

- 2026-09-20: Step 4 (evaluate) completed. v0 random_forest clears the
  success bar; chain done through this pass.
