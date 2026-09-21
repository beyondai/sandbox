"""
Monkey-mode fast baseline for the KKBOX Music Recommendation
(WSDM 2018 Kaggle) repeat-listen prediction task.

Binary classification: predict P(target=1) that a user will
listen to a given song again within the observation window, for
each (user, song) pair in train.csv.

Fast defaults used (see report.md for full rationale):
  - median-impute numeric nulls, most-frequent-impute categoricals
  - standard-scale numerics, one-hot low-cardinality categoricals
  - single model: RandomForestClassifier, modest n_estimators, no
    hyperparameter search
  - single random 80/20 held-out split, scored on AUC
  - sampled subset of train.csv for speed (see SAMPLE_ROWS below)
"""

import time

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DATA_DIR = "/Users/alex/dev/sandbox/data/kkbox/extracted"
SAMPLE_ROWS = 600_000  # self-inferred: within the 300k-1M guidance
RANDOM_STATE = 42

t0 = time.time()

# ---------------------------------------------------------------
# Load
# ---------------------------------------------------------------
train_full = pd.read_csv(f"{DATA_DIR}/train.csv")
print(f"train.csv full shape: {train_full.shape}")

if len(train_full) > SAMPLE_ROWS:
    train = train_full.sample(n=SAMPLE_ROWS, random_state=RANDOM_STATE)
else:
    train = train_full
print(f"sampled shape: {train.shape}")

members = pd.read_csv(f"{DATA_DIR}/members.csv")
songs = pd.read_csv(f"{DATA_DIR}/songs.csv")
song_extra = pd.read_csv(f"{DATA_DIR}/song_extra_info.csv")

# ---------------------------------------------------------------
# Join minimal extra raw features
# ---------------------------------------------------------------
df = train.merge(members, on="msno", how="left")
df = df.merge(songs, on="song_id", how="left")
df = df.merge(song_extra[["song_id", "isrc"]], on="song_id", how="left")

# derive a simple country-code proxy from isrc (first 2 chars) -
# a low-cardinality categorical, no elaborate parsing
df["isrc_country"] = df["isrc"].astype(str).str[:2]

# registration_init_time / expiration_date are int-encoded dates
# (YYYYMMDD) in members.csv - kept as raw numeric, no date parsing
numeric_features = [
    "song_length",
    "bd",  # self-reported age, known to have outliers/nulls
    "registration_init_time",
    "expiration_date",
]
categorical_features = [
    "source_system_tab",
    "source_screen_name",
    "source_type",
    "city",
    "gender",
    "registered_via",
    "language",
    "isrc_country",
]

target_col = "target"

for col in numeric_features:
    if col not in df.columns:
        df[col] = np.nan
for col in categorical_features:
    if col not in df.columns:
        df[col] = "unknown"

X = df[numeric_features + categorical_features]
y = df[target_col]

print(f"feature matrix shape: {X.shape}, positive rate: {y.mean():.4f}")

# ---------------------------------------------------------------
# Split
# ---------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
)

# ---------------------------------------------------------------
# Preprocess + model pipeline
# ---------------------------------------------------------------
numeric_pipe = Pipeline(
    [
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ]
)
categorical_pipe = Pipeline(
    [
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ]
)
preprocess = ColumnTransformer(
    [
        ("num", numeric_pipe, numeric_features),
        ("cat", categorical_pipe, categorical_features),
    ]
)

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    n_jobs=-1,
    random_state=RANDOM_STATE,
)

pipe = Pipeline([("preprocess", preprocess), ("model", model)])

# ---------------------------------------------------------------
# Train + eval
# ---------------------------------------------------------------
pipe.fit(X_train, y_train)
val_probs = pipe.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, val_probs)

elapsed = time.time() - t0
print(f"Held-out AUC: {auc:.4f}")
print(f"Total elapsed: {elapsed:.1f}s")

# ---------------------------------------------------------------
# Quick feature-importance readout (informs "next steps", not
# part of the eval loop)
# ---------------------------------------------------------------
feature_names = pipe.named_steps["preprocess"].get_feature_names_out()
importances = pipe.named_steps["model"].feature_importances_
order = np.argsort(importances)[::-1][:15]
print("Top 15 feature importances:")
for i in order:
    print(f"  {feature_names[i]}: {importances[i]:.4f}")

print("Null rate in joined feature columns:")
print(X.isnull().mean().sort_values(ascending=False).to_string())
