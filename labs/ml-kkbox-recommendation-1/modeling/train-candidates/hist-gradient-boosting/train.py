"""
HistGradientBoostingClassifier candidate for the KKBOX repeat-listen
prediction task.

Trains sklearn's native histogram-based gradient boosting classifier on
the full 112-column engineered feature table
(modeling/datasets/kkbox_train_features.csv) using 5-fold stratified CV,
scoring ROC AUC.

Chosen as the gradient-boosted-tree candidate per design/high-level.md's
V1 phase and the monkey-mode fast baseline, both of which point to
gradient-boosted trees (LightGBM/XGBoost) as the recommended next model
class after a plain Random Forest baseline. LightGBM failed to import on
this machine (missing the system libomp library, not fixable via a quick
Python-package install), so HistGradientBoostingClassifier is used
instead -- functionally comparable for tabular data, zero extra system
dependencies.

HistGradientBoostingClassifier handles NaN natively, so no imputation is
performed -- this is verified below by fitting on the raw (non-imputed)
feature table and confirming no error is raised.

Thread usage is bounded via OMP_NUM_THREADS (set before numpy/sklearn
import) since 3 candidates train concurrently on an 8-core machine.
"""
import os

# Bound native thread pools before numpy/sklearn are imported -- 3
# candidates train concurrently on an 8-core machine.
os.environ.setdefault("OMP_NUM_THREADS", "2")

import json
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score

DATA_PATH = "modeling/datasets/kkbox_train_features.csv"
OUT_DIR = "modeling/train-candidates/hist-gradient-boosting"

RANDOM_STATE = 42
MAX_ITER = 200


def main():
    df = pd.read_csv(DATA_PATH)

    y = df["target"]
    X = df.drop(columns=["row_id", "target"])

    null_counts = X.isnull().sum()
    nan_columns = sorted(null_counts[null_counts > 0].index.tolist())
    print(f"Rows: {len(X)}, Features: {X.shape[1]}")
    print(f"Target positive rate: {y.mean():.4f}")
    print(f"Columns containing NaN (left as-is, no imputation): {nan_columns}")

    clf = HistGradientBoostingClassifier(
        random_state=RANDOM_STATE,
        max_iter=MAX_ITER,
    )

    # Verify native NaN handling actually works before running full CV:
    # fit on the raw (non-imputed) table and confirm no error is raised.
    clf.fit(X, y)
    print("Native NaN handling verified: fit() succeeded with no imputation.")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    start = time.time()
    scores = cross_val_score(
        HistGradientBoostingClassifier(random_state=RANDOM_STATE, max_iter=MAX_ITER),
        X, y, cv=cv, scoring="roc_auc", n_jobs=1,
    )
    elapsed = time.time() - start

    cv_auc_mean = float(np.mean(scores))
    cv_auc_std = float(np.std(scores))

    print(f"Per-fold AUC: {scores}")
    print(f"CV AUC mean: {cv_auc_mean:.4f}  std: {cv_auc_std:.4f}")
    print(f"Train wall-clock seconds: {elapsed:.1f}")

    metrics = {
        "model": "hist_gradient_boosting",
        "cv_auc_mean": cv_auc_mean,
        "cv_auc_std": cv_auc_std,
        "train_seconds": elapsed,
        "params": {
            "max_iter": MAX_ITER,
            "random_state": RANDOM_STATE,
            "cv": "StratifiedKFold(n_splits=5, shuffle=True, random_state=42)",
            "scoring": "roc_auc",
            "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS"),
        },
        "notes": (
            "Native NaN handling verified: HistGradientBoostingClassifier "
            "fit successfully with no imputation on all NaN-containing "
            f"columns ({nan_columns}), including bd (~40% NaN) and "
            "source_context_freq (~26,927 rows / 5.6% NaN). No error "
            "encountered, so no imputation was performed. "
            "Accepted limitation: msno_repeat_rate_loo, song_repeat_rate_loo, "
            "and artist_repeat_rate_loo are row-level leave-one-out "
            "aggregates computed across the entire training table rather "
            "than re-computed per CV fold, so CV folds are not perfectly "
            "statistically independent for those three columns. This is an "
            "accepted simplification for this Quick POC pass; the real "
            "generalization check happens later against a properly "
            "held-out test split built independently. "
            "Thread usage bounded via OMP_NUM_THREADS=2 since 3 candidates "
            "train concurrently on an 8-core machine."
        ),
    }

    with open(os.path.join(OUT_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Wrote {OUT_DIR}/metrics.json")


if __name__ == "__main__":
    main()
