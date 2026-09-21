"""Candidate: Logistic Regression with tuned regularization strength C=0.1.

Hypothesis: the baseline LR (F1=0.6296) uses scikit-learn's default C=1.0.
Tuning C changes the regularization strength while keeping every other
choice (features, preprocessing, split) identical to the baseline in
modeling/autoresearch/experiment.py.

Tried C=0.1 (stronger regularization) and C=10.0 (weaker regularization).
C=0.1 won: F1=0.6415 vs baseline F1=0.6296. C=10.0 tied the baseline at
F1=0.6296.

Standard-scaled numeric features + one-hot plan_tier, 80/20 stratified
split, random_state=0 - same as baseline.
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
C = 0.1


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
