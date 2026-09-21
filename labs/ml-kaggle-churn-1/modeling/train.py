"""Sequential train step: CV-compare 2 candidates named in
design/high-level.md's Phasing V1 (RandomForest baseline vs. one GBM
candidate), pick the winner by mean CV ROC-AUC, then fit the winner on
the full feature table.

Quick POC time budget: 3-fold CV (not 5), reduced tree/iteration counts
(100 instead of 200), stated explicitly here per ml-modeling-train's
"Quick POC time budget" section.

Reads modeling/datasets/churn_train_features.csv (02-features.md's
Output table) only - dataset.test (churn_test.csv) is never read here,
that belongs to ml-modeling-evaluate.
"""

import json
import time

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

FEATURES_TABLE = "datasets/churn_train_features.csv"
MODEL_OUT = "model.joblib"
RESULTS_OUT = "03-train_cv_results.json"

N_FOLDS = 3  # Quick POC: 3-fold instead of Regular's 5-fold
RANDOM_STATE = 42

df = pd.read_csv(FEATURES_TABLE)
y = (df["Churn"] == "Yes").astype(int)
X = df.drop(columns=["Churn"])

numeric_cols = [
    "SeniorCitizen",
    "tenure",
    "MonthlyCharges",
    "TotalCharges",
    "TotalCharges_residual",
]
categorical_cols = [c for c in X.columns if c not in numeric_cols]

preprocess = ColumnTransformer(
    transformers=[
        ("num", "passthrough", numeric_cols),
        (
            "cat",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_cols,
        ),
    ]
)
# No scaling - both candidates are tree-based and monotonic-transform-
# invariant (see modeling/02-features.md).

candidates = {
    "random_forest": RandomForestClassifier(
        n_estimators=100,  # Quick POC: half Regular's 200
        max_depth=12,
        class_weight="balanced",
        n_jobs=-1,
        random_state=RANDOM_STATE,
    ),
    "hist_gradient_boosting": HistGradientBoostingClassifier(
        max_iter=100,  # Quick POC: half Regular's 200
        class_weight="balanced",
        random_state=RANDOM_STATE,
    ),
}

cv = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)

results = {}
for name, model in candidates.items():
    pipeline = Pipeline(steps=[("preprocess", preprocess), ("model", model)])
    t0 = time.time()
    scores = cross_val_score(
        pipeline, X, y, cv=cv, scoring="roc_auc", n_jobs=1
    )
    elapsed = time.time() - t0
    results[name] = {
        "cv_roc_auc_mean": float(scores.mean()),
        "cv_roc_auc_std": float(scores.std()),
        "cv_roc_auc_folds": scores.tolist(),
        "elapsed_seconds": round(elapsed, 1),
    }
    print(f"{name}: mean={scores.mean():.4f} std={scores.std():.4f} "
          f"({elapsed:.1f}s)")

with open(RESULTS_OUT, "w") as f:
    json.dump(results, f, indent=2)

winner_name = max(results, key=lambda k: results[k]["cv_roc_auc_mean"])
print(f"\nwinner: {winner_name}")

winner_pipeline = Pipeline(
    steps=[("preprocess", preprocess), ("model", candidates[winner_name])]
)
t0 = time.time()
winner_pipeline.fit(X, y)
fit_elapsed = time.time() - t0
print(f"final fit on full train table: {fit_elapsed:.1f}s")

joblib.dump(
    {"pipeline": winner_pipeline, "winner_name": winner_name}, MODEL_OUT
)
print(f"saved {MODEL_OUT}")
