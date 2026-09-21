"""Current best: Random Forest, n_estimators=200, max_depth=12.

Full train+eval code every autoresearch round branches from. Seeded from
modeling/03-train.md's winning candidate (modeling/train-candidates/
random-forest/train_final.py) and modeling/04-evaluate.json's metrics.

Quick POC mode: single train/test split (not CV), matching how this
project's 03-train.md/04-evaluate.md were actually produced.

Path note: this file lives at modeling/autoresearch/experiment.py, so
PROJECT_DIR is parents[2] of this file. A promoted candidate file lives 3
directories deeper (modeling/autoresearch/rounds/round-NNNN/candidate-<id>/)
- adjust this index when promoting.
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

PROJECT_DIR = Path(__file__).resolve().parents[2]
TRAIN_PATH = PROJECT_DIR / "modeling/datasets/kkbox_train_features.csv"
TEST_PATH = PROJECT_DIR / "modeling/datasets/kkbox_test_features.csv"
RANDOM_STATE = 42


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
    X_train, y_train = train.drop(columns=["row_id", "target"]), train["target"]
    X_test, y_test = test.drop(columns=["row_id", "target"]), test["target"]

    model = build_model()
    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)

    metrics = {
        "auc_roc": roc_auc_score(y_test, proba),
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred),
        "recall": recall_score(y_test, pred),
        "f1": f1_score(y_test, pred),
        "train_seconds": time.time() - t0,
    }
    print(metrics)
    return metrics


if __name__ == "__main__":
    main()
