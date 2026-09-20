"""Candidate: Logistic Regression + engineered binary feature `had_payment_failure`.

Hypothesis: payment_failures_last_90d is highly skewed (skew=1.72 per 01-data.json);
adding a binary flag (payment_failures_last_90d > 0) alongside the raw numeric features
may help a linear model capture the "any failure at all" signal more directly.

Same data, same 80/20 stratified split (test_size=0.2, random_state=0), same
LogisticRegression(class_weight="balanced", max_iter=1000, random_state=0) as the
current best in modeling/autoresearch/experiment.py.
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
NUMERIC = ["tenure_months", "monthly_usage_hours", "support_tickets_last_90d", "payment_failures_last_90d", "had_payment_failure"]
CATEGORICAL = ["plan_tier"]


def main():
    df = pd.read_csv(DATA_PATH)
    df["had_payment_failure"] = (df["payment_failures_last_90d"] > 0).astype(int)

    X, y = df.drop(columns=["churned"]), df["churned"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)

    pre = ColumnTransformer([("num", StandardScaler(), NUMERIC), ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)])
    model = Pipeline([("pre", pre), ("clf", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=0))])
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
