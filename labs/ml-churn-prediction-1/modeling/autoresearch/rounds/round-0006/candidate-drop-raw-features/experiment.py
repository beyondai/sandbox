"""Candidate: Logistic Regression (C=0.1) with raw redundant columns dropped.

Hypothesis: ticket_rate and usage_per_tenure are rate-normalized versions of
support_tickets_last_90d and monthly_usage_hours relative to tenure_months.
Now that those engineered features exist, the raw tenure_months,
monthly_usage_hours, and support_tickets_last_90d columns are redundant with
them. Dropping the raw columns and keeping only payment_failures_last_90d,
ticket_rate, usage_per_tenure, and plan_tier may reduce overfitting risk on
this small dataset (fewer, less-redundant features).

Everything else matches the current-best candidate in
modeling/autoresearch/experiment.py: same data, same split (80/20 stratified,
random_state=0), same model (LogisticRegression, C=0.1, class_weight=
"balanced", max_iter=1000, random_state=0). ticket_rate and usage_per_tenure
are still computed from the raw columns before those raw columns are
excluded from the feature list.

Note on DATA_PATH: this file lives 5 directories under the project root
(modeling/autoresearch/rounds/round-0006/candidate-drop-raw-features/), not 2
like modeling/autoresearch/experiment.py, so it uses parents[5] rather than
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
    "payment_failures_last_90d",
    "ticket_rate",
    "usage_per_tenure",
]
CATEGORICAL = ["plan_tier"]
C = 0.1


def main():
    df = pd.read_csv(DATA_PATH)
    df["ticket_rate"] = df["support_tickets_last_90d"] / (df["tenure_months"] + 1)
    df["usage_per_tenure"] = df["monthly_usage_hours"] / (df["tenure_months"] + 1)
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
