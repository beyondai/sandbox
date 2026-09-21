"""
Random Forest candidate for the KKBOX repeat-listen prediction task.

Trains RandomForestClassifier on the full 112-column engineered feature
table (modeling/datasets/kkbox_train_features.csv) using 5-fold stratified
CV, scoring ROC AUC. Writes metrics.json alongside this script.

This candidate is a direct comparison point against the monkey-mode fast
baseline (same model class, n_estimators=200 / max_depth=12, but trained
on only 12 raw columns with no feature engineering, which scored
AUC 0.6727). This run holds the model class fixed and swaps in the full
engineered feature table to isolate the effect of feature engineering.
"""
import json
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score

DATA_PATH = "modeling/datasets/kkbox_train_features.csv"
OUT_DIR = "modeling/train-candidates/random-forest"

RANDOM_STATE = 42
N_ESTIMATORS = 200
MAX_DEPTH = 12
N_JOBS = 2  # capped: 3 candidates training concurrently on an 8-core machine

def main():
    df = pd.read_csv(DATA_PATH)

    y = df["target"]
    X = df.drop(columns=["row_id", "target"])

    # Identify and median-impute every column that actually contains NaN
    # (not just `bd`, which is expected to be ~40% NaN from masked invalid
    # ages). RandomForestClassifier cannot accept NaN inputs.
    null_counts = X.isnull().sum()
    imputed_columns = sorted(null_counts[null_counts > 0].index.tolist())
    for col in imputed_columns:
        median_val = X[col].median()
        X[col] = X[col].fillna(median_val)

    assert X.isnull().sum().sum() == 0, "NaNs remain after imputation"

    print(f"Rows: {len(X)}, Features: {X.shape[1]}")
    print(f"Target positive rate: {y.mean():.4f}")
    print(f"Columns imputed (median): {imputed_columns}")

    clf = RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        max_depth=MAX_DEPTH,
        random_state=RANDOM_STATE,
        n_jobs=N_JOBS,
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    start = time.time()
    scores = cross_val_score(clf, X, y, cv=cv, scoring="roc_auc", n_jobs=1)
    elapsed = time.time() - start

    cv_auc_mean = float(np.mean(scores))
    cv_auc_std = float(np.std(scores))

    print(f"Per-fold AUC: {scores}")
    print(f"CV AUC mean: {cv_auc_mean:.4f}  std: {cv_auc_std:.4f}")
    print(f"Train wall-clock seconds: {elapsed:.1f}")

    metrics = {
        "model": "random_forest",
        "cv_auc_mean": cv_auc_mean,
        "cv_auc_std": cv_auc_std,
        "train_seconds": elapsed,
        "params": {
            "n_estimators": N_ESTIMATORS,
            "max_depth": MAX_DEPTH,
            "random_state": RANDOM_STATE,
            "n_jobs": N_JOBS,
            "cv": "StratifiedKFold(n_splits=5, shuffle=True, random_state=42)",
            "scoring": "roc_auc",
        },
        "notes": (
            "Params (n_estimators=200, max_depth=12) held identical to the "
            "monkey-mode fast baseline for direct comparability; that "
            "baseline scored AUC 0.6727 on 12 raw columns with no feature "
            "engineering, this run uses the full 112-column engineered "
            "feature table to isolate the effect of feature engineering "
            "with the model class held fixed. "
            "NaN handling: median-imputed every column found to contain "
            "NaN, not just `bd` (~40% NaN from masked invalid ages) as "
            "expected -- also found and imputed "
            f"{imputed_columns}, matching the counts flagged by a prior "
            "exploratory pass (17 rows each for artist_repeat_rate_loo, "
            "artist_count, song_length_log, artist_name_freq; ~26,927 rows "
            "/ 5.6% for source_context_freq). No rows were dropped. "
            "Accepted limitation: msno_repeat_rate_loo, song_repeat_rate_loo, "
            "and artist_repeat_rate_loo are row-level leave-one-out "
            "aggregates computed across the entire training table rather "
            "than re-computed per CV fold, so CV folds are not perfectly "
            "statistically independent for those three columns specifically. "
            "This is an accepted simplification for this Quick POC; the "
            "real generalization check happens later against a properly "
            "held-out test split built independently. n_jobs capped at 2 "
            "(rather than -1) because 3 candidates trained concurrently on "
            "an 8-core machine."
        ),
    }

    with open(f"{OUT_DIR}/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Wrote {OUT_DIR}/metrics.json")


if __name__ == "__main__":
    main()
