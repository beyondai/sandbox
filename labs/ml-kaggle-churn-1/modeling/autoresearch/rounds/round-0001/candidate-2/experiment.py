"""Autoresearch current-best: the hist_gradient_boosting pipeline that
won ml-modeling-train (03-train.md) and was scored in ml-modeling-evaluate
(04-evaluate.md). Quick POC autoresearch mode: single train/test split
(the same split churn_train_features.csv / churn_test.csv already use),
not cross-validation.

Candidate 2 (round 1): hypothesis is that the engineered column
`TotalCharges_residual` is low-signal (MI 0.0096 per 02-features.md) and
can be dropped without hurting held-out AUC-ROC. Everything else is
unchanged from the seed script.

Every round's candidates branch from a copy of this file. Paths are
relative to this file's own location, which for this candidate is
modeling/autoresearch/rounds/round-0001/candidate-2/ — four directory
levels below modeling/ (autoresearch/, rounds/, round-0001/,
candidate-2/), so HERE.parents[3] is used to land back on modeling/
instead of HERE.parent (verified empirically: parents[0]=round-0001,
parents[1]=rounds, parents[2]=autoresearch, parents[3]=modeling).
"""

import json
import sys
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

HERE = Path(__file__).resolve().parent
PROJECT_MODELING = HERE.parents[3]  # modeling/
sys.path.insert(0, str(PROJECT_MODELING))
from engineer_features import add_engineered_features  # noqa: E402

TRAIN_FEATURES = PROJECT_MODELING / "datasets" / "churn_train_features.csv"
TEST_SOURCE = PROJECT_MODELING / "datasets" / "churn_test.csv"

NUMERIC_COLS = [
    "SeniorCitizen",
    "tenure",
    "MonthlyCharges",
    "TotalCharges",
]


def build_pipeline(categorical_cols):
    preprocess = ColumnTransformer(
        transformers=[
            ("num", "passthrough", NUMERIC_COLS),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_cols,
            ),
        ]
    )
    model = HistGradientBoostingClassifier(
        max_iter=100, class_weight="balanced", random_state=42
    )
    return Pipeline(steps=[("preprocess", preprocess), ("model", model)])


def run():
    train_df = pd.read_csv(TRAIN_FEATURES)
    y_train = (train_df["Churn"] == "Yes").astype(int)
    X_train = train_df.drop(columns=["Churn"])
    X_train = X_train.drop(columns=["TotalCharges_residual"])
    categorical_cols = [c for c in X_train.columns if c not in NUMERIC_COLS]

    test_df = pd.read_csv(TEST_SOURCE)
    test_df = add_engineered_features(test_df).drop(columns=["id"])
    y_test = (test_df["Churn"] == "Yes").astype(int)
    X_test = test_df.drop(columns=["Churn"])
    X_test = X_test.drop(columns=["TotalCharges_residual"])

    pipeline = build_pipeline(categorical_cols)
    pipeline.fit(X_train, y_train)

    test_proba = pipeline.predict_proba(X_test)[:, 1]
    test_pred = (test_proba >= 0.5).astype(int)

    metrics = {
        "auc_roc": round(float(roc_auc_score(y_test, test_proba)), 4),
        "accuracy": round(float(accuracy_score(y_test, test_pred)), 4),
        "precision": round(float(precision_score(y_test, test_pred)), 4),
        "recall": round(float(recall_score(y_test, test_pred)), 4),
        "f1": round(float(f1_score(y_test, test_pred)), 4),
    }
    return metrics


if __name__ == "__main__":
    metrics = run()
    print(json.dumps(metrics, indent=2))
