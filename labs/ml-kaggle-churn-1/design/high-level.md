# Kaggle Churn — High-level Design (Quick POC)

Draft mode: Quick POC. Each item below is the single most-likely answer,
flagged where it is an assumption rather than something stated in the PRD.

## ML framing

**One sentence**: predict, per customer row, the probability that
`Churn = Yes` — a binary classification problem — from the customer's
account, contract, service, and billing attributes.

- **Prediction target**: `P(Churn = Yes | customer features)`, a
  probability in [0, 1] (the Kaggle submission format), thresholded to a
  Yes/No label only for diagnostic metrics (accuracy, precision/recall),
  never for the primary ROC-AUC metric.
- **Label definition and horizon** (assumption — not stated by Kaggle):
  `Churn` is a static, already-observed outcome baked into `train.csv` at
  data-generation time — there is no explicit "churned within N days"
  horizon the way a production churn model would define one. Treat this as
  "did this customer churn as of the snapshot," inherited from the classic
  Telco Customer Churn framing this Playground Series dataset is derived
  from, not a forward-looking prediction window. This differs from a real
  production churn system, which would need an explicit horizon (e.g.
  "will churn in the next 30 days") — worth calling out explicitly if this
  design doc is ever used as an interview-prep stand-in for a production
  system.
- **Scoring population and cadence**: one-time batch scoring of every row
  in `test.csv` (254,655 rows) for competition submission. Not a
  recurring/production cadence — there is no "new customer arrives, score
  them" trigger here, since this is a fixed Kaggle dataset, not a live
  feed.
- **Unit of prediction**: one row = one customer (`id`), one score.
- **Known exclusions / contamination**: none confirmed yet. Carried over
  from the monkey-mode baseline's open item — `id` was dropped as a
  presumed non-predictive row identifier without being explicitly tested
  for leakage; that verification is deferred to the deep dive /
  `ml-modeling-features`, not resolved here.

Single model, single project folder — no fork into multiple models, so no
"This folder builds: <model>" line is needed.

Primary metric: ROC-AUC (see `prd/kaggle-churn.md`, Metrics — offline).

## Architecture

This project has no real online serving surface (per the PRD, Metrics —
online is N/A — it's a one-shot Kaggle submission, not a deployed
service). The two diagrams below are still kept separate per this skill's
requirement, with "online inference" reinterpreted as the batch-scoring /
submission path rather than a live request/response API — flagged as an
assumption worth a quick ADR (offered below) since it reframes what
"online" means for this project.

### Offline training

```
train.csv (594,194 rows, local file:
/Users/alex/dev/sandbox/data/playground-series-churn/train.csv)
        |
        v
+----------------------+
| Load + clean          |  pandas read_csv; median-impute numeric
|                        |  nulls, mode-impute categorical nulls
|                        |  (defensive - 0 nulls observed); drop `id`
+----------------------+
        |
        v
+----------------------+
| Feature pipeline       | StandardScaler on 4 numeric cols
| (fit on train only)    | (SeniorCitizen, tenure, MonthlyCharges,
|                        | TotalCharges); OneHotEncoder on 15
|                        | low-cardinality categorical cols
+----------------------+
        |
        v
+----------------------+
| Stratified 80/20 split | preserves 77.5% No / 22.5% Yes balance
| -> train / val         | in both halves
+----------------------+
        |            \
        v             v
+--------------+   +----------------+
| Model         |   | Validation      | ROC-AUC (primary), accuracy,
| training      |-->| (held-out val)  | precision/recall, confusion
| (tree         |   |                 | matrix
| ensemble)     |   +----------------+
+--------------+
        |
        v
  serialized model artifact
  (fitted pipeline: preprocess + model)
```

### Batch scoring (this project's "online inference" equivalent)

```
test.csv (254,655 rows, unlabeled, local file:
/Users/alex/dev/sandbox/data/playground-series-churn/test.csv)
        |
        v
+----------------------+
| Same feature pipeline | transform only (fitted on train.csv,
| as training            | never refit here)
+----------------------+
        |
        v
+----------------------+
| Trained model artifact | predict_proba(X_test)[:, 1]
+----------------------+
        |
        v
+----------------------+
| Format submission      | id,Churn probability - matches
|                        | sample_submission.csv's schema exactly
+----------------------+
        |
        v
  submission.csv --> Kaggle leaderboard (public/private ROC-AUC)
```

## Phasing

- **V0 — baseline** (done via monkey-mode, see
  `monkey-mode/report.md`): fast-default pipeline (median/mode impute,
  standard-scale + one-hot, single untuned `RandomForestClassifier`, 300
  trees), full 594,194-row train set, no sampling. **Result: 0.9049
  ROC-AUC** on a held-out 20% split. Timeline: same day. Headcount: 1
  (solo).
- **V1 — first real model**: resolve the two open items the baseline
  flagged — verify `id` is non-predictive (drop with evidence, not
  assumption), and check `TotalCharges`/`tenure`/`MonthlyCharges` for
  redundancy (TotalCharges ~= tenure * MonthlyCharges) rather than feeding
  all three in raw form. Compare the baseline RandomForest against one
  gradient-boosted-tree candidate (e.g. LightGBM/XGBoost) under proper
  cross-validation instead of a single split, and tune the decision
  threshold to address the recall/precision gap on churners (61.7% recall
  vs. 68.9% precision at the default 0.5 threshold) if the use case
  favors catching churners. Timeline: within this POC's time-box (a few
  hours, same session or next). Headcount: 1.
- **V2 — stretch**: light ensembling/stacking across model families,
  probability calibration, and a real submission run against
  `test.csv` in `sample_submission.csv`'s exact format. Explicitly
  out-of-scope per the PRD unless time remains after V1 — this is a
  stretch phase, not a committed deliverable. Timeline: opportunistic.
  Headcount: 1.

## Change log

(none yet)
