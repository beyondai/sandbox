"""Candidate: tuned HistGradientBoostingClassifier.

Hypothesis: the earlier HGB run (max_iter=200, default learning_rate=0.1, no
early stopping) badly underperformed (fold-safe AUC 0.6126) because it was
undertrained/untuned, not because the model class is unsuited to this
problem. A slower learning rate with many more boosting rounds and early
stopping to pick the right number of rounds should do much better.

Quick POC mode: single train/test split (not CV), matching
modeling/autoresearch/experiment.py.

Path note: this file lives at
modeling/autoresearch/rounds/round-0001/candidate-hgb-tuned/train.py, so
PROJECT_DIR is parents[5] of this file.
"""

from pathlib import Path
import time

import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.pipeline import Pipeline

PROJECT_DIR = Path(__file__).resolve().parents[5]
TRAIN_PATH = PROJECT_DIR / "modeling/datasets/kkbox_train_features.csv"
TEST_PATH = PROJECT_DIR / "modeling/datasets/kkbox_test_features.csv"
RANDOM_STATE = 42

HYPERPARAMS = dict(
    random_state=RANDOM_STATE,
    learning_rate=0.05,
    max_iter=500,
    early_stopping=True,
    n_iter_no_change=20,
    validation_fraction=0.1,
)


def build_model():
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("clf", HistGradientBoostingClassifier(**HYPERPARAMS)),
    ])


def main():
    t0 = time.time()
    train = pd.read_csv(TRAIN_PATH)
    test = pd.read_csv(TEST_PATH)
    X_train, y_train = train.drop(columns=["row_id", "target"]), train["target"]
    X_test, y_test = test.drop(columns=["row_id", "target"]), test["target"]

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
            "A tuned HistGradientBoostingClassifier (lower learning_rate, "
            "more max_iter, early_stopping) will beat the RF baseline, "
            "unlike the earlier untuned HGB run that underperformed."
        ),
    }
    best_auc = 0.7361436524739464
    diff = metrics["auc_roc"] - best_auc
    if diff > 0:
        verdict = f"Beat baseline: auc_roc {metrics['auc_roc']:.6f} vs {best_auc:.6f} (+{diff:.6f})."
    else:
        verdict = f"Did not beat baseline: auc_roc {metrics['auc_roc']:.6f} vs {best_auc:.6f} ({diff:.6f})."
    metrics["verdict"] = verdict

    print(metrics)
    return metrics


if __name__ == "__main__":
    main()
