"""Round 1 candidate: drop the gender_* one-hot columns.

Hypothesis: modeling/02-features.md kept gender_female/gender_male/gender_missing
despite monkey-mode/report.md flagging gender as low-importance and 40% null,
reasoning a tree-based model would naturally down-weight it. That check was
flagged for ml-modeling-train but never actually done. This script drops the
three gender_* columns from the feature set and retrains the same Random
Forest (n_estimators=200, max_depth=12, random_state=42) to see if auc_roc
improves, worsens, or stays about the same.

Same method as modeling/autoresearch/experiment.py: single train/test split
(Quick POC mode, no CV), median imputation + RandomForestClassifier.
"""

from pathlib import Path
import time

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.pipeline import Pipeline

# This file lives at modeling/autoresearch/rounds/round-0001/candidate-drop-gender/,
# so PROJECT_DIR is parents[5] of this file.
PROJECT_DIR = Path(__file__).resolve().parents[5]
TRAIN_PATH = PROJECT_DIR / "modeling/datasets/kkbox_train_features.csv"
TEST_PATH = PROJECT_DIR / "modeling/datasets/kkbox_test_features.csv"
RANDOM_STATE = 42

DROP_COLUMNS = ["row_id", "target"]
GENDER_COLUMNS = ["gender_female", "gender_male", "gender_missing"]


def build_model():
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("clf", RandomForestClassifier(
            n_estimators=200, max_depth=12, random_state=RANDOM_STATE, n_jobs=4
        )),
    ])


def main():
    t0 = time.time()
    train = pd.read_csv(TRAIN_PATH)
    test = pd.read_csv(TEST_PATH)

    drop_cols = DROP_COLUMNS + GENDER_COLUMNS
    X_train, y_train = train.drop(columns=drop_cols), train["target"]
    X_test, y_test = test.drop(columns=drop_cols), test["target"]

    model = build_model()
    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)

    train_seconds = time.time() - t0

    metrics = {
        "auc_roc": roc_auc_score(y_test, proba),
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred),
        "recall": recall_score(y_test, pred),
        "f1": f1_score(y_test, pred),
        "train_seconds": train_seconds,
        "hypothesis": (
            "Dropping the low-signal, 40%-null gender_* one-hot columns "
            "(gender_female, gender_male, gender_missing) will not hurt, and "
            "may slightly help, Random Forest auc_roc versus the full feature set."
        ),
    }

    baseline_auc = 0.7361436524739464
    delta = metrics["auc_roc"] - baseline_auc
    if delta > 0:
        verdict = (
            f"Beat baseline: auc_roc {metrics['auc_roc']:.6f} vs "
            f"{baseline_auc:.6f} baseline (+{delta:.6f})."
        )
    elif delta < 0:
        verdict = (
            f"Did not beat baseline: auc_roc {metrics['auc_roc']:.6f} vs "
            f"{baseline_auc:.6f} baseline ({delta:.6f})."
        )
    else:
        verdict = f"Tied baseline exactly at auc_roc {metrics['auc_roc']:.6f}."
    metrics["verdict"] = verdict

    # Bonus: check feature_importances_ for gender_* as supporting evidence
    # (they are absent here since we dropped them, so this is a no-op check
    # left in for documentation purposes only - see experiment.py's run for
    # actual importances if needed).

    print(metrics)
    return metrics


if __name__ == "__main__":
    main()
