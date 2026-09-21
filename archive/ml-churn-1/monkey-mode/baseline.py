"""Monkey-mode churn baseline: predict churn at lifetime day 28.

Label: churned=1 if a player has zero activity rows in lifetime days 28..55
(inclusive), else 0. Features use only activity/purchases with lifetime day
< 28 plus static player attributes. Players are kept only if their full label
window is observable (signup_day + 55 <= 269).
"""
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import (average_precision_score, f1_score,
                             precision_recall_curve, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

DATA = "/Users/alex/dev/sandbox/data/riot-synthetic/synthetic-data/data/lifecycle/"
CUTOFF = 28          # prediction point: lifetime day 28
LABEL_END = 55       # label window: lifetime days 28..55 inclusive
MAX_DAY = 269        # last observed absolute day
SEED = 42

t0 = time.time()
players = pd.read_csv(DATA + "players.csv")
activity = pd.read_csv(DATA + "activity.csv")
purchases = pd.read_csv(DATA + "purchases.csv")
print(f"players={len(players):,} activity={len(activity):,} purchases={len(purchases):,}")
print(f"activity day range: {activity.day.min()}..{activity.day.max()}")

# ---- lifetime day -------------------------------------------------------
signup = players.set_index("player_id")["signup_day"]
activity["lt_day"] = activity["day"] - activity["player_id"].map(signup)
purchases["lt_day"] = purchases["day"] - purchases["player_id"].map(signup)
assert (activity.lt_day >= 0).all(), "activity before signup"

# ---- cohort filter: full label window observable ------------------------
elig = players[players.signup_day + LABEL_END <= MAX_DAY].copy()
print(f"eligible players (signup_day+{LABEL_END}<=269): {len(elig):,} of {len(players):,}")

# ---- label ---------------------------------------------------------------
act_label = activity[(activity.lt_day >= CUTOFF) & (activity.lt_day <= LABEL_END)]
active_in_window = act_label.groupby("player_id").size()
elig["churned"] = (~elig.player_id.isin(active_in_window.index)).astype(int)

# ---- features from lifetime days 0..27 -----------------------------------
pre = activity[activity.lt_day < CUTOFF]
g = pre.groupby("player_id")
feat = pd.DataFrame({
    "active_days": g.size(),
    "total_games": g["games"].sum(),
    "total_wins": g["wins"].sum(),
    "total_party_games": g["party_games"].sum(),
    "total_minutes": g["minutes"].sum(),
    "last_active_day": g["lt_day"].max(),
    "first_active_day": g["lt_day"].min(),
})
feat["win_rate"] = feat.total_wins / feat.total_games.replace(0, np.nan)
feat["party_share"] = feat.total_party_games / feat.total_games.replace(0, np.nan)
feat["days_since_last_activity"] = CUTOFF - feat.last_active_day
last7 = pre[pre.lt_day >= CUTOFF - 7].groupby("player_id")
feat["active_days_last7"] = last7.size()
feat["games_last7"] = last7["games"].sum()

pp = purchases[purchases.lt_day < CUTOFF].groupby("player_id")
feat["n_purchases"] = pp.size()
feat["total_spend"] = pp["amount_usd"].sum()

df = elig.merge(feat, left_on="player_id", right_index=True, how="left")
never_engaged = df.active_days.isna()
# Cleaning: no activity -> 0 for counts; recency for never-engaged = full window
fill0 = ["active_days", "total_games", "total_wins", "total_party_games",
         "total_minutes", "active_days_last7", "games_last7", "n_purchases",
         "total_spend"]
df[fill0] = df[fill0].fillna(0)
df["days_since_last_activity"] = df["days_since_last_activity"].fillna(CUTOFF)
df["first_active_day"] = df["first_active_day"].fillna(CUTOFF)
df["last_active_day"] = df["last_active_day"].fillna(-1)
df["win_rate"] = df["win_rate"].fillna(df["win_rate"].median())
df["party_share"] = df["party_share"].fillna(df["party_share"].median())
df["any_purchase"] = (df.n_purchases > 0).astype(int)

pos_all = df.churned.mean()
pos_engaged = df.loc[~never_engaged, "churned"].mean()
print(f"never-engaged players (0 activity in days 0..27): {never_engaged.sum():,} "
      f"({never_engaged.mean():.1%}); their churn rate: {df.loc[never_engaged,'churned'].mean():.3f}")
print(f"positive rate (all eligible): {pos_all:.4f}  n={len(df):,}")
print(f"positive rate (excluding never-engaged): {pos_engaged:.4f}  n={(~never_engaged).sum():,}")

num_cols = fill0 + ["win_rate", "party_share", "days_since_last_activity",
                    "first_active_day", "last_active_day", "any_purchase", "signup_day"]
cat = pd.get_dummies(df[["region", "platform", "acquisition_source"]], dtype=int)
X = pd.concat([df[num_cols], cat], axis=1)
y = df.churned.values
print(f"feature matrix: {X.shape}")

# ---- split 70/15/15 stratified ------------------------------------------
X_tr, X_tmp, y_tr, y_tmp = train_test_split(X, y, test_size=0.30, stratify=y, random_state=SEED)
X_va, X_te, y_va, y_te = train_test_split(X_tmp, y_tmp, test_size=0.50, stratify=y_tmp, random_state=SEED)
scaler = StandardScaler().fit(X_tr[num_cols])
for part in (X_tr, X_va, X_te):
    part[num_cols] = scaler.transform(part[num_cols])
print(f"split sizes train/val/test: {len(X_tr)}/{len(X_va)}/{len(X_te)}")

# ---- model ---------------------------------------------------------------
model = HistGradientBoostingClassifier(random_state=SEED).fit(X_tr, y_tr)

# threshold: maximize F1 on validation
p_va = model.predict_proba(X_va)[:, 1]
prec, rec, thr = precision_recall_curve(y_va, p_va)
f1s = 2 * prec[:-1] * rec[:-1] / np.clip(prec[:-1] + rec[:-1], 1e-9, None)
best_thr = float(thr[np.argmax(f1s)])
print(f"val PR-AUC={average_precision_score(y_va, p_va):.4f} best-F1 threshold={best_thr:.4f} (val F1={f1s.max():.4f})")

# ---- test ----------------------------------------------------------------
p_te = model.predict_proba(X_te)[:, 1]
pred = (p_te >= best_thr).astype(int)
pr_auc = average_precision_score(y_te, p_te)
roc = roc_auc_score(y_te, p_te)
P, R, F = precision_score(y_te, pred), recall_score(y_te, pred), f1_score(y_te, pred)
pos_te = y_te.mean()
print("\n=== TEST RESULTS ===")
print(f"positive rate (test): {pos_te:.4f}   PR-AUC random ref = {pos_te:.4f}")
print(f"PR-AUC: {pr_auc:.4f}   ROC-AUC: {roc:.4f}")
print(f"@thr={best_thr:.4f}: precision={P:.4f} recall={R:.4f} F1={F:.4f}")
bar_pr = pr_auc >= 2 * pos_te
bar_roc = roc >= 0.75
print(f"success bar: PR-AUC>=2x pos rate ({2*pos_te:.4f}) -> {bar_pr}; ROC-AUC>=0.75 -> {bar_roc}; "
      f"VERDICT: {'PASS' if bar_pr and bar_roc else 'FAIL'}")

# ---- permutation importance on test --------------------------------------
pi = permutation_importance(model, X_te, y_te, scoring="average_precision",
                            n_repeats=5, random_state=SEED, n_jobs=-1)
imp = pd.Series(pi.importances_mean, index=X.columns).sort_values(ascending=False)
print("\ntop-10 permutation importance (drop in test PR-AUC):")
print(imp.head(10).round(4).to_string())

# ---- grading-key sanity check (read-only, post-eval, not a feature) ------
truth = pd.read_csv(DATA + "_truth/players_truth.csv")[["player_id", "state_at_cutoff"]]
chk = df[["player_id", "churned"]].merge(truth, on="player_id")
print("\n[grading-key check] label rate by _truth state_at_cutoff:")
print(chk.groupby("state_at_cutoff").churned.agg(["mean", "size"]).round(3).to_string())
print(f"\nruntime: {time.time()-t0:.1f}s")
