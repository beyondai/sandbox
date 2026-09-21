"""Build the labeled train/test tables for the riot-churn v0 model.

Label source: the synthetic dataset's own ground-truth snapshot
(_truth/players_truth.csv, state_at_cutoff), computed at the single global
cutoff_day=180 recorded in _truth/params.csv. That cutoff is fixed by the
generator, not a per-player relative horizon.

Feature cutoff is set at day 120, not day 180: design/high-level.md's ML
framing specifies a 60-day forward horizon (score a player, then look 60
days ahead for the outcome). Scoring at day 120 and labeling at day 180
implements that horizon directly (120 + 60 = 180). This also matters for a
reason found empirically: the monkey-mode baseline for this same project
scored features computed right up to the label day itself and got a
near-perfect, near-tautological result (recency features - "already stopped
playing" - dominated, because the feature window and the label window ended
on the same day). Moving the feature cutoff 60 days earlier than the label
means the model has to predict an outcome that has not happened yet in the
feature window, which is the actual task described in high-level.md.

campaign.csv is excluded: send_day is 180 for every row (at or after both
cutoffs used here), and it is out of scope as a feature per
design/high-level.md's Architecture regardless. content_calendar.csv is not
per-player and is excluded too.
"""
import numpy as np
import pandas as pd

DATA = "/Users/alex/dev/sandbox/data/riot-synthetic/synthetic-data/data/lifecycle"
LABEL_DAY = 180        # fixed by the synthetic generator's cutoff_day
HORIZON_DAYS = 60      # per design/high-level.md's ML framing
FEATURE_CUTOFF = LABEL_DAY - HORIZON_DAYS  # = 120: last day features may use
GRACE_DAYS = 14        # onboarding grace period exclusion, per high-level
SEED = 42
TEST_SHARE = 0.2

players = pd.read_csv(f"{DATA}/players.csv")
activity = pd.read_csv(f"{DATA}/activity.csv")
purchases = pd.read_csv(f"{DATA}/purchases.csv")
truth = pd.read_csv(f"{DATA}/_truth/players_truth.csv")

activity = activity[activity["day"] < FEATURE_CUTOFF]
purchases = purchases[purchases["day"] < FEATURE_CUTOFF]

# --- activity features (all strictly before FEATURE_CUTOFF) ---
agg = activity.groupby("player_id").agg(
    active_days=("day", "nunique"),
    total_games=("games", "sum"),
    total_wins=("wins", "sum"),
    total_party_games=("party_games", "sum"),
    total_minutes=("minutes", "sum"),
    last_active_day=("day", "max"),
)
agg["win_rate"] = np.where(
    agg["total_games"] > 0, agg["total_wins"] / agg["total_games"], 0.0
)
agg["days_since_last_active"] = FEATURE_CUTOFF - agg["last_active_day"]

half = FEATURE_CUTOFF / 2
first_half = activity[activity["day"] < half].groupby("player_id")["games"].sum()
second_half = activity[activity["day"] >= half].groupby("player_id")["games"].sum()
agg["activity_trend"] = (
    second_half.reindex(agg.index, fill_value=0)
    - first_half.reindex(agg.index, fill_value=0)
)

# --- purchase features (all strictly before FEATURE_CUTOFF) ---
pagg = purchases.groupby("player_id").agg(
    total_spend=("amount_usd", "sum"),
    purchase_count=("amount_usd", "count"),
    distinct_item_types=("item_type", "nunique"),
    last_purchase_day=("day", "max"),
)
pagg["days_since_last_purchase"] = FEATURE_CUTOFF - pagg["last_purchase_day"]

# --- assemble ---
df = players.set_index("player_id").copy()
df["tenure_at_scoring"] = FEATURE_CUTOFF - df["signup_day"]
df = df.join(agg, how="left").join(pagg, how="left")

activity_cols = [
    "active_days", "total_games", "total_wins", "total_party_games",
    "total_minutes", "win_rate", "days_since_last_active", "activity_trend",
]
purchase_cols = [
    "total_spend", "purchase_count", "distinct_item_types",
    "days_since_last_purchase",
]
# players with no activity/purchase rows before the feature cutoff: 0
# activity, and "never purchased" sentinel distance equal to their full
# tenure at scoring time (no purchase to be recent about).
df[activity_cols] = df[activity_cols].fillna(0.0)
df["days_since_last_purchase"] = df["days_since_last_purchase"].fillna(
    df["tenure_at_scoring"]
)
df[["total_spend", "purchase_count", "distinct_item_types"]] = df[
    ["total_spend", "purchase_count", "distinct_item_types"]
].fillna(0.0)

label_map = {"active": 0, "lapsed": 1, "churned": 1}
truth = truth.set_index("player_id")
df["label"] = truth["state_at_cutoff"].map(label_map)

before = len(df)
# exclude players who had not yet signed up by FEATURE_CUTOFF, or who signed
# up too recently before it (onboarding grace period - too new to score).
df = df[df["signup_day"] <= FEATURE_CUTOFF - GRACE_DAYS].copy()
excluded_grace = before - len(df)

assert df["label"].isna().sum() == 0, "unmatched player_id between players and truth"

pos_rate = df["label"].mean()
assert 0.05 < pos_rate < 0.95, f"degenerate positive rate: {pos_rate:.3f}"

df = df.reset_index()

rng = np.random.default_rng(SEED)
test_mask = np.zeros(len(df), dtype=bool)
for label_val in df["label"].unique():
    idx = df.index[df["label"] == label_val].to_numpy().copy()
    rng.shuffle(idx)
    n_test = int(round(len(idx) * TEST_SHARE))
    test_mask[idx[:n_test]] = True

train_df = df[~test_mask].drop(columns=["last_active_day", "last_purchase_day"])
test_df = df[test_mask].drop(columns=["last_active_day", "last_purchase_day"])

train_df.to_csv("modeling/datasets/churn_train.csv", index=False)
test_df.to_csv("modeling/datasets/churn_test.csv", index=False)

print(f"feature cutoff day: {FEATURE_CUTOFF}  label day: {LABEL_DAY}  horizon: {HORIZON_DAYS}")
print(f"rows before grace exclusion: {before}")
print(f"excluded (signed up after day {FEATURE_CUTOFF - GRACE_DAYS}): {excluded_grace}")
print(f"rows after exclusion: {len(df)}")
print(f"positive rate (label=1, left): {pos_rate:.4f}")
print(f"train rows: {len(train_df)}  test rows: {len(test_df)}")
print(f"train positive rate: {train_df['label'].mean():.4f}")
print(f"test positive rate: {test_df['label'].mean():.4f}")
