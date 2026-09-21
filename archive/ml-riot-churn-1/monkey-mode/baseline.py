"""
Monkey-mode fast baseline: 28-day lapse-risk prediction for recently-active players.

Task definition (user-answered, see report.md Requirements section):
- Cutoff day c. Population = players whose LAST activity day strictly before c
  falls in [c-7, c) (active in trailing week before cutoff).
- Label = 1 (lapsed) if player has ZERO activity rows with day in [c, c+28); else 0.
- Only activity rows with day < c are used to build features AND population.
- Train cutoff c=135 (labels from day 135-162).
- Test cutoff c=180 (labels from day 180-207); exclude players in campaign.csv
  with treated=1 at test cutoff only (comeback-offer contamination).
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, precision_score, recall_score, f1_score

DATA_DIR = "/Users/alex/dev/sandbox/data/riot-synthetic/synthetic-data/data/lifecycle"

players = pd.read_csv(f"{DATA_DIR}/players.csv")
activity = pd.read_csv(f"{DATA_DIR}/activity.csv")
campaign = pd.read_csv(f"{DATA_DIR}/campaign.csv")

print(f"players.csv rows: {len(players)}")
print(f"activity.csv rows: {len(activity)}")
print(f"campaign.csv rows: {len(campaign)}")

players["region"] = players["region"].fillna("unknown")


def build_dataset(c, exclude_treated=False):
    """Build population + features + labels for cutoff day c."""
    # Features/population MUST only use day < c (no look-ahead).
    hist = activity[activity["day"] < c]
    # future window for labels
    future = activity[(activity["day"] >= c) & (activity["day"] < c + 28)]

    # last activity day per player, strictly before c
    last_day = hist.groupby("player_id")["day"].max().rename("last_activity_day")

    # population: last activity day in [c-7, c)
    pop = last_day[(last_day >= c - 7) & (last_day < c)].index
    pop_df = pd.DataFrame({"player_id": pop})

    if exclude_treated:
        treated_ids = set(campaign.loc[campaign["treated"] == 1, "player_id"])
        pop_df = pop_df[~pop_df["player_id"].isin(treated_ids)]

    # label: 1 if zero future activity rows in [c, c+28)
    future_players = set(future["player_id"].unique())
    pop_df["label"] = (~pop_df["player_id"].isin(future_players)).astype(int)

    # trailing-28d window for features: [c-28, c)
    trail = hist[hist["day"] >= c - 28]
    trail_agg = trail.groupby("player_id").agg(
        active_days_28d=("day", "nunique"),
        games_28d=("games", "sum"),
        wins_28d=("wins", "sum"),
        party_games_28d=("party_games", "sum"),
        minutes_28d=("minutes", "sum"),
    ).reset_index()
    trail_agg["win_rate_28d"] = np.where(
        trail_agg["games_28d"] > 0, trail_agg["wins_28d"] / trail_agg["games_28d"], 0.0
    )
    trail_agg["party_share_28d"] = np.where(
        trail_agg["games_28d"] > 0, trail_agg["party_games_28d"] / trail_agg["games_28d"], 0.0
    )

    df = pop_df.merge(trail_agg, on="player_id", how="left")
    df = df.merge(
        last_day.rename("last_activity_day").reset_index(), on="player_id", how="left"
    )
    df["days_since_last_active"] = c - df["last_activity_day"]

    df = df.merge(players, on="player_id", how="left")
    df["tenure"] = c - df["signup_day"]

    # median-impute any remaining numeric nulls (players with no trailing activity edge case)
    numeric_cols = [
        "active_days_28d", "games_28d", "wins_28d", "party_games_28d",
        "minutes_28d", "win_rate_28d", "party_share_28d",
        "days_since_last_active", "tenure",
    ]
    for col in numeric_cols:
        df[col] = df[col].fillna(df[col].median())

    return df, numeric_cols


train_df, numeric_cols = build_dataset(c=135, exclude_treated=False)
test_df, _ = build_dataset(c=180, exclude_treated=True)

train_churn_rate = train_df["label"].mean()
test_churn_rate = test_df["label"].mean()

print(f"\nTrain population (c=135): {len(train_df)} players, churn rate = {train_churn_rate:.4f}")
print(f"Test population (c=180, treated excluded): {len(test_df)} players, churn rate = {test_churn_rate:.4f}")

# Sanity check per task instructions: churn rate must NOT be near 0% or 100%.
assert 0.02 < train_churn_rate < 0.5, f"SUSPICIOUS train churn rate: {train_churn_rate}"
assert 0.02 < test_churn_rate < 0.5, f"SUSPICIOUS test churn rate: {test_churn_rate}"
print("Sanity check passed: churn rates are in a plausible range (not near 0% or 100%).")

categorical_cols = ["region", "platform", "acquisition_source"]

preprocessor = ColumnTransformer([
    ("num", Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ]), numeric_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
])

model = Pipeline([
    ("prep", preprocessor),
    ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
])

X_train = train_df[numeric_cols + categorical_cols]
y_train = train_df["label"]
X_test = test_df[numeric_cols + categorical_cols]
y_test = test_df["label"]

model.fit(X_train, y_train)

y_proba = model.predict_proba(X_test)[:, 1]
y_pred = (y_proba >= 0.5).astype(int)

pr_auc = average_precision_score(y_test, y_proba)
precision = precision_score(y_test, y_pred, zero_division=0)
recall = recall_score(y_test, y_pred, zero_division=0)
f1 = f1_score(y_test, y_pred, zero_division=0)

print(f"\n=== Results (test cutoff c=180) ===")
print(f"PR-AUC:    {pr_auc:.4f}")
print(f"Precision: {precision:.4f} (threshold=0.5)")
print(f"Recall:    {recall:.4f} (threshold=0.5)")
print(f"F1:        {f1:.4f} (threshold=0.5)")
print(f"Success bar: PR-AUC >= 0.30 -> {'MET' if pr_auc >= 0.30 else 'NOT MET'}")

# Also report predicted-positive rate at threshold 0.5 for context (class_weight=balanced
# shifts effective threshold behavior)
print(f"\nPredicted positive rate @0.5: {y_pred.mean():.4f}")
print(f"Actual positive rate (test): {y_test.mean():.4f}")

results = {
    "n_players_csv": len(players),
    "n_activity_rows": len(activity),
    "n_campaign_rows": len(campaign),
    "train_cutoff": 135,
    "test_cutoff": 180,
    "train_n": len(train_df),
    "train_churn_rate": train_churn_rate,
    "test_n": len(test_df),
    "test_churn_rate": test_churn_rate,
    "pr_auc": pr_auc,
    "precision": precision,
    "recall": recall,
    "f1": f1,
    "pred_pos_rate": float(y_pred.mean()),
}
import json
with open("/Users/alex/dev/sandbox/labs/ml-riot-churn-1/monkey-mode/results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nWrote results.json")
