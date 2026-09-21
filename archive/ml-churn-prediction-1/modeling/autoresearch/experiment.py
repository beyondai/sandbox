"""Candidate: small MLPClassifier (16,8) neural network, on the exact same
feature set and split as the current-best candidate in
modeling/autoresearch/experiment.py.

Hypothesis: a small neural network can capture nonlinear interactions among
the engineered features (ticket_rate, usage_per_tenure) that a linear model
misses, potentially improving on Logistic Regression C=0.1 (F1=0.6792).

Everything else matches the current-best candidate: same data, same split
(80/20 stratified, random_state=0), same numeric feature list (including
ticket_rate and usage_per_tenure) and categorical feature (plan_tier).
Model swapped to sklearn.neural_network.MLPClassifier(hidden_layer_sizes=
(16,8), max_iter=500, random_state=0). Note: MLPClassifier has no
class_weight parameter, so class imbalance is not explicitly corrected for
here (unlike the LogisticRegression baseline's class_weight="balanced").

Note on DATA_PATH: this file lives 5 directories under the project root
(modeling/autoresearch/rounds/round-0006/candidate-mlp/), not 2 like
modeling/autoresearch/experiment.py, so it uses parents[2] rather than
parents[2] to correctly resolve to monkey-mode/data.csv at the project root.
"""
import json
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DATA_PATH = Path(__file__).resolve().parents[2] / "monkey-mode" / "data.csv"
NUMERIC = [
    "tenure_months",
    "monthly_usage_hours",
    "support_tickets_last_90d",
    "payment_failures_last_90d",
    "ticket_rate",
    "usage_per_tenure",
]
CATEGORICAL = ["plan_tier"]


def main():
    df = pd.read_csv(DATA_PATH)
    df["ticket_rate"] = df["support_tickets_last_90d"] / (df["tenure_months"] + 1)
    df["usage_per_tenure"] = df["monthly_usage_hours"] / (df["tenure_months"] + 1)
    X, y = df.drop(columns=["churned"]), df["churned"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)

    pre = ColumnTransformer([("num", StandardScaler(), NUMERIC), ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)])
    model = Pipeline([("pre", pre), ("clf", MLPClassifier(hidden_layer_sizes=(16, 8), max_iter=500, random_state=0))])
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
