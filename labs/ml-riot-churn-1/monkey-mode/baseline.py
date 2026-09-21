"""
Monkey-mode fast baseline: binary churn classification for the riot-synthetic
lifecycle dataset.

Task: did a player stay (active) or leave (lapsed/churned) by day 180?
Label: _truth/players_truth.csv, state_at_cutoff -> active=0, lapsed/churned=1.

Leakage exclusions:
- campaign.csv: a day-180 re-engagement intervention targeted at players who
  are already lapsing. Using it (or any column derived from it) would leak
  the label. Excluded entirely.
- content_calendar.csv: a global (not per-player) signal. Skipped for a fast
  baseline.
- _truth/players_truth.csv columns other than state_at_cutoff (social,
  engage, payer_initial, payer_at_cutoff, spend_rate, amount_mu,
  days_lapsed_at_cutoff): these are hidden generative parameters used to
  SIMULATE the data, not observable signals a real system would have at
  scoring time. Excluded from features.
- activity.csv / purchases.csv: only rows with day < 180 (the cutoff) are
  used to build features, so no post-cutoff information leaks in.
"""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, roc_auc_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DATA_ROOT = (
    "/Users/alex/dev/sandbox/data/riot-synthetic/synthetic-data/data/lifecycle"
)
CUTOFF_DAY = 180
RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
players = pd.read_csv(f"{DATA_ROOT}/players.csv")
activity = pd.read_csv(f"{DATA_ROOT}/activity.csv")
purchases = pd.read_csv(f"{DATA_ROOT}/purchases.csv")
truth = pd.read_csv(f"{DATA_ROOT}/_truth/players_truth.csv")

print(f"players: {players.shape}, activity: {activity.shape}, "
      f"purchases: {purchases.shape}, truth: {truth.shape}")

# ---------------------------------------------------------------------------
# Label
# ---------------------------------------------------------------------------
label = truth[["player_id", "state_at_cutoff"]].copy()
label["left"] = (label["state_at_cutoff"] != "active").astype(int)
print("\nRaw state_at_cutoff counts:")
print(label["state_at_cutoff"].value_counts())
print("\nBinary label counts (0=stayed, 1=left):")
print(label["left"].value_counts())

# ---------------------------------------------------------------------------
# Pre-cutoff activity features
# ---------------------------------------------------------------------------
act = activity[activity["day"] < CUTOFF_DAY].copy()

agg = act.groupby("player_id").agg(
    total_games=("games", "sum"),
    total_wins=("wins", "sum"),
    total_party_games=("party_games", "sum"),
    total_minutes=("minutes", "sum"),
    mean_games_per_active_day=("games", "mean"),
    mean_minutes_per_active_day=("minutes", "mean"),
    active_days=("day", "count"),
    last_active_day=("day", "max"),
)

first_half = act[act["day"] < CUTOFF_DAY / 2].groupby("player_id").agg(
    first_half_minutes=("minutes", "sum"),
    first_half_games=("games", "sum"),
)
second_half = act[act["day"] >= CUTOFF_DAY / 2].groupby("player_id").agg(
    second_half_minutes=("minutes", "sum"),
    second_half_games=("games", "sum"),
)

activity_feat = (
    agg.join(first_half, how="left")
    .join(second_half, how="left")
    .reset_index()
)
activity_feat[["first_half_minutes", "first_half_games",
               "second_half_minutes", "second_half_games"]] = (
    activity_feat[["first_half_minutes", "first_half_games",
                    "second_half_minutes", "second_half_games"]].fillna(0)
)
activity_feat["activity_trend_minutes"] = (
    activity_feat["second_half_minutes"] - activity_feat["first_half_minutes"]
)
activity_feat["activity_trend_games"] = (
    activity_feat["second_half_games"] - activity_feat["first_half_games"]
)
activity_feat["win_rate"] = np.where(
    activity_feat["total_games"] > 0,
    activity_feat["total_wins"] / activity_feat["total_games"],
    0.0,
)
activity_feat["party_rate"] = np.where(
    activity_feat["total_games"] > 0,
    activity_feat["total_party_games"] / activity_feat["total_games"],
    0.0,
)
activity_feat["days_since_last_activity"] = (
    CUTOFF_DAY - activity_feat["last_active_day"]
)

# ---------------------------------------------------------------------------
# Pre-cutoff purchase features
# ---------------------------------------------------------------------------
pur = purchases[purchases["day"] < CUTOFF_DAY].copy()
purchase_feat = pur.groupby("player_id").agg(
    total_spend=("amount_usd", "sum"),
    purchase_count=("amount_usd", "count"),
    distinct_item_types=("item_type", "nunique"),
    offer_purchase_rate=("offer_price", "mean"),
).reset_index()

# ---------------------------------------------------------------------------
# Assemble the modeling table (one row per player, all 12000 players)
# ---------------------------------------------------------------------------
df = players.merge(activity_feat, on="player_id", how="left")
df = df.merge(purchase_feat, on="player_id", how="left")
df = df.merge(label[["player_id", "left"]], on="player_id", how="left")

activity_cols = [
    "total_games", "total_wins", "total_party_games", "total_minutes",
    "mean_games_per_active_day", "mean_minutes_per_active_day",
    "active_days", "first_half_minutes", "first_half_games",
    "second_half_minutes", "second_half_games", "activity_trend_minutes",
    "activity_trend_games", "win_rate", "party_rate",
]
# No activity rows before cutoff == zero activity, not "unknown" -> fill 0.
df[activity_cols] = df[activity_cols].fillna(0)
# No activity at all: treat as maximally stale (never active).
df["last_active_day"] = df["last_active_day"].fillna(-1)
df["days_since_last_activity"] = df["days_since_last_activity"].fillna(
    CUTOFF_DAY - (-1)
)

purchase_cols = ["total_spend", "purchase_count", "distinct_item_types",
                  "offer_purchase_rate"]
df[purchase_cols] = df[purchase_cols].fillna(0)

# True missing categorical -> explicit "Unknown" category (29% of players
# have a null region; dropping them would throw away too much data).
df["region"] = df["region"].fillna("Unknown")

# signup_day is fully populated (checked), but median-impute defensively.
df["signup_day"] = df["signup_day"].fillna(df["signup_day"].median())

numeric_features = [
    "signup_day",
] + activity_cols + ["last_active_day", "days_since_last_activity"] + purchase_cols

categorical_features = ["region", "platform", "acquisition_source"]

X = df[numeric_features + categorical_features]
y = df["left"]

print(f"\nModeling table: {df.shape[0]} players, "
      f"{len(numeric_features)} numeric + {len(categorical_features)} "
      f"categorical features")
print("Any nulls left in X?", X.isnull().sum().sum())

# ---------------------------------------------------------------------------
# Train / test split
# ---------------------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
)

preprocess = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
    ]
)

model = Pipeline(steps=[
    ("preprocess", preprocess),
    ("clf", RandomForestClassifier(
        n_estimators=300, max_depth=8, min_samples_leaf=5,
        random_state=RANDOM_STATE, n_jobs=-1,
    )),
])

model.fit(X_train, y_train)

y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

f1 = f1_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_proba)

print("\n=== Held-out test set (20%, n={}) ===".format(len(y_test)))
print(f"F1: {f1:.4f}")
print(f"ROC-AUC: {auc:.4f}")
print("\nClassification report:")
print(classification_report(y_test, y_pred, target_names=["stayed", "left"]))

# ---------------------------------------------------------------------------
# Feature importance (RandomForest, post-encoding)
# ---------------------------------------------------------------------------
ohe = model.named_steps["preprocess"].named_transformers_["cat"]
cat_names = list(ohe.get_feature_names_out(categorical_features))
all_feature_names = numeric_features + cat_names
importances = model.named_steps["clf"].feature_importances_
imp_series = pd.Series(importances, index=all_feature_names).sort_values(
    ascending=False
)
print("\nTop 10 feature importances:")
print(imp_series.head(10))
