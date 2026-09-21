"""Final fit of the winning Random Forest candidate on the full training
table - no CV here, just the deployable model. The CV-leakage issue found
during candidate comparison (see 03-train.md) only affects reusing a
pre-built feature table ACROSS folds; a single fit on the whole table has
no folds to cross-contaminate, so the original kkbox_train_features.csv
(post-bug-fix, see 02-features.md's Change log) is used as-is here.

ml-modeling-evaluate is what actually validates this against the held-out
test split - this script just produces the artifact to hand it.
"""

import time

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

FEAT_PATH = "modeling/datasets/kkbox_train_features.csv"
OUT_PATH = "modeling/train-candidates/random-forest/model.joblib"

t0 = time.time()
df = pd.read_csv(FEAT_PATH)
X = df.drop(columns=["row_id", "target"])
y = df["target"]

model = Pipeline([
    ("impute", SimpleImputer(strategy="median")),
    ("clf", RandomForestClassifier(
        n_estimators=200, max_depth=12, random_state=42, n_jobs=4
    )),
])
model.fit(X, y)
elapsed = time.time() - t0

joblib.dump(model, OUT_PATH)
print(f"fit on {len(df)} rows, {X.shape[1]} features in {elapsed:.1f}s")
print(f"model saved to {OUT_PATH}")
