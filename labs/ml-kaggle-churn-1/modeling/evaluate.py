"""Evaluate the winning pipeline on the held-out churn_test.csv split.

dataset.test (churn_test.csv) is read only here, for the first time in
the chain - never touched by ml-modeling-data's profiling,
ml-modeling-features, or ml-modeling-train.

Applies the same pure, row-wise feature-engineering function used on
train (add_engineered_features from engineer_features.py) so the fitted
pipeline sees the same columns it was trained on. No leakage risk: that
function uses no train-fitted statistic.
"""

import json

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from engineer_features import add_engineered_features

TEST_SOURCE = "datasets/churn_test.csv"
TRAIN_FEATURES = "datasets/churn_train_features.csv"
MODEL_PATH = "model.joblib"
OUT_JSON = "04-evaluate.json"

bundle = joblib.load(MODEL_PATH)
pipeline = bundle["pipeline"]
winner_name = bundle["winner_name"]

# ---- Test split ----
test_df = pd.read_csv(TEST_SOURCE)
test_df = add_engineered_features(test_df).drop(columns=["id"])
y_test = (test_df["Churn"] == "Yes").astype(int)
X_test = test_df.drop(columns=["Churn"])

test_proba = pipeline.predict_proba(X_test)[:, 1]
test_pred = (test_proba >= 0.5).astype(int)

test_metrics = {
    "accuracy": accuracy_score(y_test, test_pred),
    "precision": precision_score(y_test, test_pred),
    "recall": recall_score(y_test, test_pred),
    "f1": f1_score(y_test, test_pred),
    "auc_roc": roc_auc_score(y_test, test_proba),
}

# ---- Train-side number for the overfit gap (same table the model was
# fit on in ml-modeling-train) ----
train_df = pd.read_csv(TRAIN_FEATURES)
y_train = (train_df["Churn"] == "Yes").astype(int)
X_train = train_df.drop(columns=["Churn"])
train_proba = pipeline.predict_proba(X_train)[:, 1]
train_pred = (train_proba >= 0.5).astype(int)
train_auc = roc_auc_score(y_train, train_proba)
train_f1 = f1_score(y_train, train_pred)

# ---- Naive baselines on the test split ----
majority_class = y_test.mode()[0]
majority_pred = pd.Series(majority_class, index=y_test.index)
baseline_metrics = {
    "majority_class_accuracy": accuracy_score(y_test, majority_pred),
    "majority_class_f1": f1_score(
        y_test, majority_pred, zero_division=0
    ),
    "random_auc_roc": 0.5,  # a non-informative classifier's expectation
}

results = {
    "winner_name": winner_name,
    "primary_metric": "auc_roc",
    "metrics": {k: round(float(v), 4) for k, v in test_metrics.items()},
    "baseline_metrics": {
        k: round(float(v), 4) for k, v in baseline_metrics.items()
    },
    "overfit_gap": {
        "train_auc_roc": round(float(train_auc), 4),
        "test_auc_roc": round(float(test_metrics["auc_roc"]), 4),
        "gap": round(float(train_auc - test_metrics["auc_roc"]), 4),
        "train_f1": round(float(train_f1), 4),
        "test_f1": round(float(test_metrics["f1"]), 4),
    },
}

with open(OUT_JSON, "w") as f:
    json.dump(results, f, indent=2)

print(json.dumps(results, indent=2))
print(f"\ntest rows scored: {len(y_test)}")
print(f"test class balance: {y_test.value_counts(normalize=True).to_dict()}")
