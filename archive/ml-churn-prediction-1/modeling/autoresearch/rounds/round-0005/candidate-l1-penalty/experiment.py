"""Candidate: Logistic Regression (C=0.1) with L1 (sparsity-inducing) penalty
instead of the default L2, keeping all existing features including
ticket_rate.

Hypothesis: prior rounds already swept C-strength (0.01/0.03/0.1/10, all with
default L2 penalty) without beating the current best. This round changes the
regularization TYPE instead of its strength: L1 does implicit feature
selection by zeroing out coefficients for uninformative features, which may
reduce overfitting/noise from the one-hot encoded plan_tier columns and
improve generalization on the test split.

Everything else matches the current-best candidate in
modeling/autoresearch/experiment.py: same data, same split (80/20 stratified,
random_state=0), same features (including ticket_rate), same C=0.1 and
class_weight="balanced". The only change is penalty="l1" with solver=
"liblinear" (liblinear is required for L1 support).

Note on DATA_PATH: this file lives 5 directories under the project root
(modeling/autoresearch/rounds/round-0005/candidate-l1-penalty/), not 2 like
modeling/autoresearch/experiment.py, so it uses parents[5] rather than
parents[2] to correctly resolve to monkey-mode/data.csv at the project root.
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
NUMERIC = [
    "tenure_months",
    "monthly_usage_hours",
    "support_tickets_last_90d",
    "payment_failures_last_90d",
    "ticket_rate",
]
CATEGORICAL = ["plan_tier"]
C = 0.1


def main():
    df = pd.read_csv(DATA_PATH)
    df["ticket_rate"] = df["support_tickets_last_90d"] / (df["tenure_months"] + 1)
    X, y = df.drop(columns=["churned"]), df["churned"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)

    pre = ColumnTransformer([("num", StandardScaler(), NUMERIC), ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)])
    model = Pipeline([
        ("pre", pre),
        ("clf", LogisticRegression(C=C, penalty="l1", solver="liblinear", class_weight="balanced", max_iter=1000, random_state=0)),
    ])
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
