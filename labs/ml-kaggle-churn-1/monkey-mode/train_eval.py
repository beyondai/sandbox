"""
Monkey-mode baseline for the Kaggle playground churn competition.

Fast, real, end-to-end baseline: load -> clean -> encode -> split ->
train (RandomForestClassifier) -> evaluate (ROC-AUC + extras).

Run with: uv run python3 monkey-mode/train_eval.py
(from /Users/alex/dev/sandbox/labs/ml-kaggle-churn-1/)
"""
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

elapsed = time.time() - t0

results = {
    "input": {
        "data_path": DATA_PATH,
        "n_rows": int(n_rows),
        "n_cols": int(n_cols),
        "total_nulls": total_nulls,
        "class_balance_pct": {k: round(v * 100, 2) for k, v in class_balance.items()},
        "class_counts": {k: int(v) for k, v in class_counts.items()},
        "numeric_cols": numeric_cols,
        "categorical_cols": categorical_cols,
    },
    "split": {
        "train_rows": int(len(X_train)),
        "val_rows": int(len(X_val)),
        "test_size": 0.20,
    },
    "results": {
        "roc_auc": roc_auc,
        "accuracy": accuracy,
        "confusion_matrix": cm,
        "confusion_matrix_labels": ["No (0)", "Yes (1)"],
        "top_feature_importances": feat_imp,
    },
    "elapsed_seconds": elapsed,
}

with open(OUT_JSON, "w") as f:
    json.dump(results, f, indent=2)

print(json.dumps(results, indent=2))
print(f"\nDone in {elapsed:.1f}s")
