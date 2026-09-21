"""
Train candidate: Logistic Regression (linear baseline) for KKBOX repeat-listen
prediction (binary classification, AUC primary metric).

Part of a 3-way parallel model comparison (Logistic Regression vs Random
Forest vs HistGradientBoostingClassifier). This script trains/evaluates only
the Logistic Regression candidate.

Method: 5-fold stratified CV (StratifiedKFold, shuffle=True, random_state=42),
scoring ROC AUC per fold. Pipeline = SimpleImputer(median) -> StandardScaler
-> LogisticRegression(max_iter=1000, random_state=42). n_jobs capped at 2
since 3 candidates train concurrently on an 8-core machine.

NaN handling: bd (~40% NaN, invalid ages masked upstream) plus a handful of
other columns found to have NaN in this table (artist_repeat_rate_loo,
artist_count, song_length_log, artist_name_freq - 17 rows each - and
source_context_freq - ~26,927 rows, 5.6%) are all median-imputed via a single
SimpleImputer over all numeric feature columns (row_id and target excluded).

Known accepted limitation (not fixed here): msno_repeat_rate_loo,
song_repeat_rate_loo, and artist_repeat_rate_loo are leave-one-out aggregates
computed across the *entire* training table, not re-computed per CV fold.
This makes CV folds mildly non-independent for those three columns. Accepted
simplification for this Quick POC; real generalization check happens later
against an independently built held-out test split.
"""
import json
import time

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DATA_PATH = "modeling/datasets/kkbox_train_features.csv"
OUT_DIR = "modeling/train-candidates/logistic-regression"

RANDOM_STATE = 42
N_SPLITS = 5
N_JOBS = 2

df = pd.read_csv(DATA_PATH)

y = df["target"]
X = df.drop(columns=["target", "row_id"])

# Confirm which columns actually contain NaN in this run (for metrics.json notes).
nan_counts = X.isna().sum()
nan_cols = nan_counts[nan_counts > 0].sort_values(ascending=False)
print("Columns with NaN:")
print(nan_cols)

pipeline = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        (
            "clf",
            LogisticRegression(
                max_iter=1000,
                random_state=RANDOM_STATE,
            ),
        ),
    ]
)

cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)

start = time.time()
scores = cross_val_score(
    pipeline, X, y, cv=cv, scoring="roc_auc", n_jobs=N_JOBS
)
train_seconds = time.time() - start

cv_auc_mean = float(np.mean(scores))
cv_auc_std = float(np.std(scores))

print(f"Per-fold AUC: {scores}")
print(f"CV AUC mean: {cv_auc_mean:.5f}  std: {cv_auc_std:.5f}")
print(f"Train seconds: {train_seconds:.2f}")

params = {
    "model": "LogisticRegression",
    "max_iter": 1000,
    "random_state": RANDOM_STATE,
    "solver": "lbfgs",  # sklearn default for LogisticRegression
    "penalty": "l2",  # sklearn default
    "C": 1.0,  # sklearn default
    "imputer_strategy": "median",
    "scaler": "StandardScaler",
    "cv": {
        "strategy": "StratifiedKFold",
        "n_splits": N_SPLITS,
        "shuffle": True,
        "random_state": RANDOM_STATE,
    },
    "n_jobs": N_JOBS,
}

notes = (
    "Known accepted limitation: msno_repeat_rate_loo, song_repeat_rate_loo, and "
    "artist_repeat_rate_loo are leave-one-out aggregates computed across the "
    "entire training table (not re-computed per CV fold), so CV folds are not "
    "perfectly statistically independent for those three columns. Accepted "
    "simplification for this Quick POC; the real generalization check happens "
    "later against a properly held-out test split built independently. "
    f"NaN columns found and median-imputed (via a single SimpleImputer over all "
    f"numeric feature columns): {', '.join(f'{c} ({int(n)})' for c, n in nan_cols.items())}. "
    "bd (~40% NaN) was expected per the task brief; the other five columns "
    "(artist_repeat_rate_loo, artist_count, song_length_log, artist_name_freq at "
    "17 rows each, and source_context_freq at ~26,927 rows / 5.6%) were also "
    "found to have NaN and were imputed the same way rather than dropped or ignored."
)

metrics = {
    "model": "logistic_regression",
    "cv_auc_mean": cv_auc_mean,
    "cv_auc_std": cv_auc_std,
    "train_seconds": train_seconds,
    "params": params,
    "notes": notes,
}

with open(f"{OUT_DIR}/metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

print("Wrote metrics.json")
