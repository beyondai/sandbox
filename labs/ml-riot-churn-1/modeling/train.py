"""Train step: compare Logistic Regression vs. a small Random Forest via
cross-validation on the train table only (churn_train_features.csv). Both
are what design/high-level.md's V0 phase names ("baseline - logistic
regression or a single small tree ensemble"), so Quick POC's default jump to
the XGBoost/LightGBM workhorse row is overridden here per that phasing.
"""
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

train = pd.read_csv("datasets/churn_train_features.csv")
X = train.drop(columns=["player_id", "label"])
y = train["label"]

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scoring = ["f1", "roc_auc"]

candidates = {
    "logistic_regression": Pipeline([
        ("scale", StandardScaler()),
        ("clf", LogisticRegression(
            class_weight="balanced", max_iter=2000, random_state=42
        )),
    ]),
    "random_forest": RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    ),
}

results = {}
for name, model in candidates.items():
    scores = cross_validate(model, X, y, cv=cv, scoring=scoring)
    results[name] = {
        "f1_mean": float(np.mean(scores["test_f1"])),
        "f1_std": float(np.std(scores["test_f1"])),
        "roc_auc_mean": float(np.mean(scores["test_roc_auc"])),
        "roc_auc_std": float(np.std(scores["test_roc_auc"])),
    }
    print(name, results[name])

winner = max(results, key=lambda k: results[k]["roc_auc_mean"])
print("winner:", winner)

# fit the winner on the full train table, save it for the evaluate step
final_model = candidates[winner]
final_model.fit(X, y)

import pickle
with open("model.pkl", "wb") as f:
    pickle.dump({"model": final_model, "features": list(X.columns)}, f)

with open("cv_results.json", "w") as f:
    json.dump({"results": results, "winner": winner}, f, indent=2)

if winner == "random_forest":
    importances = sorted(
        zip(X.columns, final_model.feature_importances_),
        key=lambda t: t[1], reverse=True,
    )
    print("feature importances:")
    for feat, imp in importances[:10]:
        print(f"  {feat}: {imp:.4f}")
    with open("feature_importances.json", "w") as f:
        json.dump({k: float(v) for k, v in importances}, f, indent=2)
