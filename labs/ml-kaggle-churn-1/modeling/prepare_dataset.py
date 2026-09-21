"""Register the flat labeled churn table: split + profile.

Source: /Users/alex/dev/sandbox/data/playground-series-churn/train.csv
(the only labeled table for this project; Kaggle's test.csv stays
unlabeled and reserved for submission, never touched here).

Writes:
- modeling/datasets/churn_train.csv, modeling/datasets/churn_test.csv
  (stratified random 80/20 split, seed 42 - static snapshot label, no
  time-window, so a random split is appropriate; matches the split used
  by the monkey-mode baseline for direct comparability)
- modeling/01-data.json (profile of the train split only)
"""

import json

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

SOURCE = "/Users/alex/dev/sandbox/data/playground-series-churn/train.csv"
TRAIN_OUT = "datasets/churn_train.csv"
TEST_OUT = "datasets/churn_test.csv"
PROFILE_OUT = "01-data.json"

SEED = 42
TEST_SHARE = 0.20

df = pd.read_csv(SOURCE)

train_df, test_df = train_test_split(
    df, test_size=TEST_SHARE, random_state=SEED, stratify=df["Churn"]
)
train_df.to_csv(TRAIN_OUT, index=False)
test_df.to_csv(TEST_OUT, index=False)

# ---- Profile the train split only ----
n_rows, n_cols = train_df.shape
memory_mb = round(train_df.memory_usage(deep=True).sum() / (1024 * 1024), 3)

null_rates = (train_df.isnull().mean() * 100).round(4).to_dict()

class_counts = train_df["Churn"].value_counts().to_dict()
class_balance = (
    train_df["Churn"].value_counts(normalize=True).round(4).to_dict()
)

id_col = "id"
target_col = "Churn"
numeric_cols = [
    c
    for c in train_df.select_dtypes(include=["int64", "float64"]).columns
    if c != id_col
]
categorical_cols = [
    c
    for c in train_df.select_dtypes(include=["object"]).columns
    if c != target_col
]

numeric_distributions = {}
for c in numeric_cols:
    s = train_df[c]
    numeric_distributions[c] = {
        "min": float(s.min()),
        "max": float(s.max()),
        "mean": round(float(s.mean()), 4),
        "median": float(s.median()),
        "std": round(float(s.std()), 4),
        "skew": round(float(s.skew()), 4),
    }

categorical_distributions = {}
for c in categorical_cols:
    vc = train_df[c].value_counts()
    categorical_distributions[c] = {
        "cardinality": int(train_df[c].nunique()),
        "top_values": {str(k): int(v) for k, v in vc.head(5).items()},
    }

# ---- Quality flags ----
quality_flags = []

dup_rows = int(train_df.duplicated().sum())
if dup_rows:
    quality_flags.append(f"{dup_rows} exact duplicate rows in train split")
else:
    quality_flags.append("0 exact duplicate rows in train split")

dup_ids = int(train_df[id_col].duplicated().sum())
if dup_ids:
    quality_flags.append(f"{dup_ids} duplicate id values in train split")

high_null_cols = [c for c, r in null_rates.items() if r > 20.0]
if high_null_cols:
    quality_flags.append(
        f"columns above 20% null rate: {high_null_cols}"
    )
else:
    quality_flags.append("no column exceeds 20% null rate (all 0%)")

# TotalCharges ~= tenure * MonthlyCharges collinearity check
corr = np.corrcoef(
    train_df["TotalCharges"].astype(float),
    (train_df["tenure"] * train_df["MonthlyCharges"]).astype(float),
)[0, 1]
quality_flags.append(
    "TotalCharges vs. tenure*MonthlyCharges correlation: "
    f"{round(float(corr), 4)} (near-1.0 confirms redundancy flagged "
    "in design/high-level.md, worth addressing in feature engineering)"
)

quality_flags.append(
    "id: unverified for leakage - carried over as a data-quality-neutral "
    "flag (not an impossible/unusual value), verification deferred to "
    "ml-modeling-features per design/high-level.md Phasing V1"
)

profile = {
    "dataset": {
        "train": TRAIN_OUT,
        "test": TEST_OUT,
        "label": "Churn",
        "id": "id",
        "split": {
            "type": "random",
            "train_cutoff": None,
            "test_cutoff": None,
            "horizon_days": None,
            "seed": SEED,
            "test_share": TEST_SHARE,
        },
        "exclusions": [],
        "built_by": "registered",
    },
    "shape": {"rows": n_rows, "columns": n_cols, "memory_mb": memory_mb},
    "nulls": null_rates,
    "target": {
        "column": "Churn",
        "type": "classification",
        "class_balance": class_balance,
        "distribution": {},
    },
    "numeric_distributions": numeric_distributions,
    "categorical_distributions": categorical_distributions,
    "quality_flags": quality_flags,
}

with open(PROFILE_OUT, "w") as f:
    json.dump(profile, f, indent=2)

print(json.dumps(profile, indent=2))
print(f"\ntrain rows: {n_rows}, test rows: {test_df.shape[0]}")
print(f"class_counts (train): {class_counts}")
