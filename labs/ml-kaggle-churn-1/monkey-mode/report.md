# Monkey-Mode Baseline Report: Kaggle Playground Churn

## Requirements

- **Task + data** (answered by user): binary classification predicting the
  `Churn` column, using
  `/Users/alex/dev/sandbox/data/playground-series-churn/train.csv` for both
  training and held-out evaluation, and reserving
  `/Users/alex/dev/sandbox/data/playground-series-churn/test.csv` (Kaggle's
  unlabeled test set) for an eventual submission only — not used here for
  training or evaluation.
- **Primary metric** (answered by user): ROC-AUC, matching the Kaggle
  competition's own scoring.
- **Success bar** (self-inferred by the agent, NOT provided by the user):
  ~0.85-0.88 ROC-AUC on the held-out split, a reasonable first-baseline
  target for tabular customer-churn problems with a simple tree ensemble.
- **Sample size**: no sampling was needed. The full train.csv
  (**100%, 594,194 rows**) was used for the train/val split — the dataset
  was small enough to run in full in well under a minute.

## Input

- **Source**:
  `/Users/alex/dev/sandbox/data/playground-series-churn/train.csv`
  (real file, read directly with pandas).
- **Shape observed**: 594,194 rows x 21 columns.
- **Columns**: `id` (row identifier, dropped before modeling), 4 numeric
  features (`SeniorCitizen`, `tenure`, `MonthlyCharges`, `TotalCharges`),
  15 categorical features (`gender`, `Partner`, `Dependents`,
  `PhoneService`, `MultipleLines`, `InternetService`, `OnlineSecurity`,
  `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`,
  `StreamingMovies`, `Contract`, `PaperlessBilling`, `PaymentMethod`), and
  the target `Churn` (`Yes`/`No`).
- **Nulls**: 0 across all 21 columns (`df.isnull().sum()` totalled 0) —
  this dataset arrived fully populated, no imputation was actually
  exercised even though the pipeline includes it defensively.
- **Class balance observed**: `No` = 460,377 rows (77.48%), `Yes` =
  133,817 rows (22.52%) — a real but moderate imbalance, not extreme.

## Design

Fast defaults applied, as specified, with no deviation and no model
comparison:

- **Cleaning**: median-impute numeric nulls, most-frequent-impute
  categorical nulls (both defensive — the data had none in practice).
  Dropped `id` as a non-predictive row identifier.
- **Features**: `StandardScaler` on the 4 numeric columns
  (`SeniorCitizen`, `tenure`, `MonthlyCharges`, `TotalCharges`);
  `OneHotEncoder` (with `handle_unknown="ignore"`) on the 15 categorical
  columns, all low-cardinality (2-4 distinct values each). No embeddings,
  no interaction/engineered features.
- **Model**: a single `RandomForestClassifier` (300 trees, `min_samples
  _leaf=2`, `n_jobs=-1`, `random_state=42`), trained once — not compared
  against alternatives. A tree ensemble is a strong, low-effort fit for
  tabular churn data with mixed numeric/categorical features.
- **Eval split**: a stratified 80/20 train/val split of train.csv
  (475,355 train rows / 118,839 val rows), stratified on `Churn` to
  preserve the observed class balance in both halves. `test.csv` was not
  touched.

## Implementation

The actual script that ran end to end (saved at
`monkey-mode/train_eval.py`, executed via
`uv run python3 monkey-mode/train_eval.py` from the project folder using
the shared sandbox venv):

```python
import json
import time

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DATA_PATH = "/Users/alex/dev/sandbox/data/playground-series-churn/train.csv"
OUT_JSON = "/Users/alex/dev/sandbox/labs/ml-kaggle-churn-1/monkey-mode/results.json"

t0 = time.time()

# ---------------------------------------------------------------- Input ----
df = pd.read_csv(DATA_PATH)
n_rows, n_cols = df.shape
null_counts = df.isnull().sum()
total_nulls = int(null_counts.sum())
class_balance = df["Churn"].value_counts(normalize=True).to_dict()
class_counts = df["Churn"].value_counts().to_dict()

# --------------------------------------------------------------- Design ----
# Drop the row-id column (not a real feature). Target is Churn (Yes/No).
target_col = "Churn"
id_col = "id"

y = (df[target_col] == "Yes").astype(int)
X = df.drop(columns=[target_col, id_col])

numeric_cols = X.select_dtypes(include=["int64", "float64"]).columns.tolist()
categorical_cols = X.select_dtypes(include=["object", "str"]).columns.tolist()

numeric_pipeline = Pipeline(
    steps=[
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ]
)
categorical_pipeline = Pipeline(
    steps=[
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ]
)

preprocess = ColumnTransformer(
    transformers=[
        ("num", numeric_pipeline, numeric_cols),
        ("cat", categorical_pipeline, categorical_cols),
    ]
)

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=None,
    min_samples_leaf=2,
    n_jobs=-1,
    random_state=42,
)

pipeline = Pipeline(steps=[("preprocess", preprocess), ("model", model)])

# 80/20 held-out split, stratified on the target to preserve class balance.
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

# ---------------------------------------------------------- Implementation --
pipeline.fit(X_train, y_train)

val_proba = pipeline.predict_proba(X_val)[:, 1]
val_pred = (val_proba >= 0.5).astype(int)

# ------------------------------------------------------------- Results -----
roc_auc = roc_auc_score(y_val, val_proba)
accuracy = accuracy_score(y_val, val_pred)
cm = confusion_matrix(y_val, val_pred).tolist()

# Feature importances mapped back to encoded feature names.
ohe = pipeline.named_steps["preprocess"].named_transformers_["cat"].named_steps[
    "onehot"
]
cat_feature_names = ohe.get_feature_names_out(categorical_cols).tolist()
all_feature_names = numeric_cols + cat_feature_names
importances = pipeline.named_steps["model"].feature_importances_
feat_imp = sorted(
    zip(all_feature_names, importances.tolist()), key=lambda t: -t[1]
)[:15]
```

(Full script, including the results-dump tail, is at
`monkey-mode/train_eval.py`; raw output is saved at
`monkey-mode/results.json`.)

## Results

Real numbers from the executed run, on the 118,839-row held-out
validation split:

- **ROC-AUC: 0.9049** — clears the self-inferred 0.85-0.88 baseline bar
  by a comfortable margin.
- **Accuracy: 0.8510** (threshold 0.5).
- **Confusion matrix** (rows = actual, columns = predicted; labels
  `No (0)`, `Yes (1)`):

  |            | Pred No | Pred Yes |
  |------------|---------|----------|
  | Actual No  | 84,633  | 7,443    |
  | Actual Yes | 10,264  | 16,499   |

  Precision on `Yes` ~= 16,499 / (16,499 + 7,443) = 68.9%; recall on
  `Yes` ~= 16,499 / (16,499 + 10,264) = 61.7%. The model is noticeably
  better at the majority class, expected given the ~77/23 imbalance and
  the default 0.5 threshold.

- **Top feature importances** (Gini importance from the forest):

  | Feature                          | Importance |
  |-----------------------------------|-----------|
  | TotalCharges                      | 0.173     |
  | tenure                            | 0.152     |
  | MonthlyCharges                    | 0.143     |
  | PaymentMethod_Electronic check    | 0.085     |
  | Contract_Month-to-month           | 0.080     |
  | InternetService_Fiber optic       | 0.054     |
  | OnlineSecurity_No                 | 0.044     |
  | TechSupport_No                    | 0.029     |
  | Contract_Two year                 | 0.021     |
  | InternetService_DSL               | 0.016     |

  The three numeric billing/tenure features alone account for roughly
  47% of total importance.

- Training + eval on the full 594,194-row dataset took ~42 seconds on
  this machine.

## Learnings

- **The target is clearly learnable** from this feature set with no
  special tricks — a stock RandomForest on standard-scaled numerics and
  one-hot categoricals reaches 0.90 ROC-AUC, well above the self-inferred
  0.85-0.88 bar, on the first and only run.
- **No data-quality issues surfaced**: zero nulls across all 21 columns,
  `TotalCharges` parsed cleanly as float64 (the classic public Telco
  churn dataset this one resembles is known for blank/whitespace
  `TotalCharges` strings that break naive parsing — this variant did not
  have that problem).
- **`id` looks like an obvious leakage risk to check** — it was dropped
  outright without testing it, on the reasonable assumption a row
  identifier carries no real signal; worth explicitly confirming (e.g.
  correlation with target, or an ablation) in the deeper modeling pass
  rather than just assuming.
- **Billing/tenure numerics dominate**, with `TotalCharges`, `tenure`,
  and `MonthlyCharges` together contributing ~47% of feature importance.
  This is intuitively sound (mechanically, `TotalCharges` ~=
  `tenure` * `MonthlyCharges`, so the three are correlated and jointly
  informative rather than three independent signals).
- **Contract type and payment method are the strongest categorical
  signals** (`Contract_Month-to-month` and `PaymentMethod_Electronic
  check` both rank in the top 5) — consistent with known churn intuition
  that month-to-month, non-automatic-payment customers churn more.
- **Class imbalance (77.5/22.5) is real but not severe** — it shows up
  as materially lower recall (61.7%) than precision (68.9%) on the
  minority `Yes` class at the default threshold, but did not need
  resampling or class weighting to get a strong ROC-AUC, since ROC-AUC
  is threshold- and prevalence-insensitive in a way accuracy is not.

## Suggested Next Steps

- **A tree ensemble is a reasonable V1 model-class bet.** The stock
  RandomForest baseline already clears the target bar with zero tuning,
  which suggests the regular ml-system-design flow can treat gradient-
  boosted trees / random forests as the default first candidate rather
  than spending early cycles evaluating linear models or deep nets for
  this problem shape.
- **`TotalCharges`, `tenure`, and `MonthlyCharges` are worth a closer
  look in the deep dive**, both individually and as a check for
  redundancy (since `TotalCharges` ~= `tenure` * `MonthlyCharges`) — the
  design/modeling phase should decide whether to keep all three, derive
  a cleaner engineered ratio, or drop one to reduce collinearity.
- **`Contract` and `PaymentMethod` look like strong, cheap categorical
  signals** and should be kept front-and-center in feature design rather
  than treated as boilerplate one-hot columns.
- **The default-threshold recall gap on churners (62% vs. 69% precision)
  is worth flagging for the metrics section of the real design doc** —
  if the business use case cares more about catching churners than
  precision, a lower decision threshold or class-weighted training
  should be evaluated there, not just ROC-AUC.
- **Verify `id` is truly non-predictive** as an explicit checkpoint in
  the deep dive, rather than carrying forward this baseline's assumption
  unchecked.
- A submission-format prediction against
  `/Users/alex/dev/sandbox/data/playground-series-churn/test.csv` (using
  the `id,Churn` format shown in `sample_submission.csv`) was explicitly
  out of scope for this baseline exercise and would be a natural next
  step once a model is finalized.
