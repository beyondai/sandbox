"""Re-run monkey-mode's exact baseline approach (same feature set, same
preprocessing, same RandomForestClassifier config as monkey-mode/
baseline.py) but on THIS PROJECT'S actual train/test split
(modeling/datasets/kkbox_{train,test}.csv) instead of monkey-mode's own
independently-sampled 80/20 split - so it's scored on the exact same
held-out rows as the winning Random Forest in modeling/03-train.md, for a
true same-test-set comparison (04-evaluate.md flagged the original
monkey-mode/report.md number as not being one).
"""

import time

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TRAIN_PATH = "modeling/datasets/kkbox_train.csv"
TEST_PATH = "modeling/datasets/kkbox_test.csv"
RANDOM_STATE = 42

NUMERIC_FEATURES = ["song_length", "bd", "registration_init_time", "expiration_date"]
CATEGORICAL_FEATURES = [
    "source_system_tab", "source_screen_name", "source_type", "city",
    "gender", "registered_via", "language", "isrc_country",
]


def build_X_y(path):
    df = pd.read_csv(path)
    df["isrc_country"] = df["isrc"].astype(str).str[:2]
    for col in NUMERIC_FEATURES:
        if col not in df.columns:
            df[col] = np.nan
    for col in CATEGORICAL_FEATURES:
        if col not in df.columns:
            df[col] = "unknown"
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df["target"]
    return X, y


t0 = time.time()
X_train, y_train = build_X_y(TRAIN_PATH)
X_test, y_test = build_X_y(TEST_PATH)
print(f"train shape: {X_train.shape}, test shape: {X_test.shape}")
print(f"train positive rate: {y_train.mean():.4f}, "
      f"test positive rate: {y_test.mean():.4f}")

numeric_pipe = Pipeline([
    ("impute", SimpleImputer(strategy="median")),
    ("scale", StandardScaler()),
])
categorical_pipe = Pipeline([
    ("impute", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore")),
])
preprocess = ColumnTransformer([
    ("num", numeric_pipe, NUMERIC_FEATURES),
    ("cat", categorical_pipe, CATEGORICAL_FEATURES),
])
model = RandomForestClassifier(
    n_estimators=200, max_depth=12, n_jobs=4, random_state=RANDOM_STATE,
)
pipe = Pipeline([("preprocess", preprocess), ("model", model)])

pipe.fit(X_train, y_train)
test_probs = pipe.predict_proba(X_test)[:, 1]
test_pred = (test_probs >= 0.5).astype(int)
train_probs = pipe.predict_proba(X_train)[:, 1]

metrics = {
    "auc_roc": roc_auc_score(y_test, test_probs),
    "accuracy": accuracy_score(y_test, test_pred),
    "precision": precision_score(y_test, test_pred),
    "recall": recall_score(y_test, test_pred),
    "f1": f1_score(y_test, test_pred),
    "train_auc": roc_auc_score(y_train, train_probs),
}
elapsed = time.time() - t0

print(f"\nmonkey-mode approach, scored on THIS project's real test set:")
for k, v in metrics.items():
    print(f"  {k}: {v:.4f}")
print(f"elapsed: {elapsed:.1f}s")

import json
with open("modeling/monkey_mode_on_test_results.json", "w") as f:
    json.dump(metrics, f, indent=2)
