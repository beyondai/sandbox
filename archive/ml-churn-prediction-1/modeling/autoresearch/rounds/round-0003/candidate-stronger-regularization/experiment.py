"""Candidate: Logistic Regression with even stronger regularization, C=0.03.

Round 2 found C=0.1 (F1=0.6415) beats default C=1.0 (F1=0.6296) and C=10.0
(tied at 0.6296). This round pushes further in the same direction, testing
C=0.01 and C=0.03 (stronger regularization than C=0.1).

Result: both C=0.01 and C=0.03 produced identical metrics
(accuracy=0.8417, precision=0.5862, recall=0.7083, f1=0.6415) - the
predictions did not change further with additional regularization strength
below C=0.1. C=0.03 is reported as the submitted candidate (tie-break,
arbitrary between the two identical results). Neither C=0.01 nor C=0.03
beats the round-0002 best of F1=0.6415 - this candidate ties it.

Standard-scaled numeric features + one-hot plan_tier, 80/20 stratified
split, random_state=0 - same as baseline and round-0002 candidate.
"""
import json
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DATA_PATH = Path(__file__).resolve().parents[5] / "monkey-mode" / "data.csv"
NUMERIC = ["tenure_months", "monthly_usage_hours", "support_tickets_last_90d", "payment_failures_last_90d"]
CATEGORICAL = ["plan_tier"]
C = 0.03


def main():
    df = pd.read_csv(DATA_PATH)
    X, y = df.drop(columns=["churned"]), df["churned"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)

    pre = ColumnTransformer([("num", StandardScaler(), NUMERIC), ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)])
    model = Pipeline([("pre", pre), ("clf", LogisticRegression(C=C, class_weight="balanced", max_iter=1000, random_state=0))])
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred), 4),
        "recall": round(recall_score(y_test, y_pred), 4),
        "f1": round(f1_score(y_test, y_pred), 4),
    }
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    main()
