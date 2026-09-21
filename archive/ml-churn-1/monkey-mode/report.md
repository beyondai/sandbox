# Monkey-mode baseline: churn at day 28

Run date: 2026-09-20. Autonomous, single-pass baseline. Everything not stated by the user is a recorded assumption.

## Requirements

1. **Task + data** - mixed provenance.
   - *Answered by user:* "predict churn at day 28". Data source is the real lifecycle dataset at `/Users/alex/dev/sandbox/data/riot-synthetic/synthetic-data/data/lifecycle/` (no synthetic generation). `campaign.csv` is ignored per instruction. `_truth/` is never used as a modeling input.
   - *Self-inferred (operationalization):* per player, the prediction point is lifetime day 28 (absolute day `signup_day + 28`). Features use only activity/purchases with lifetime day < 28 plus static player attributes. Label `churned = 1` if the player has zero activity rows in lifetime days 28..55 inclusive (a 28-day inactivity window after the prediction point), else 0. Only players whose full label window is observable are included (`signup_day + 55 <= 269`). Players with zero activity in the first 28 days are kept as real "never engaged" cases; the label rate is reported with and without them.
2. **Primary metric** - *self-inferred:* PR-AUC (average precision) on a held-out test split. Secondary: ROC-AUC, and precision/recall/F1 at the threshold that maximizes F1 on the validation split, applied to test. The positive rate is the PR-AUC "random" reference.
3. **Success bar** - *self-inferred:* soft target PR-AUC >= 2x positive rate and ROC-AUC >= 0.75. Reasoning: a synthetic lifecycle dataset with recency/frequency signal in the first 28 days should be well above random for a simple model; this is a floor for "the target is learnable", not a production bar.

## Input

- Path: `/Users/alex/dev/sandbox/data/riot-synthetic/synthetic-data/data/lifecycle/`
- `players.csv`: 12,000 rows (player_id, signup_day, region, platform, acquisition_source). signup_day ranges 0..179.
- `activity.csv`: 748,811 rows (one row per player-day with activity), absolute day range 0..269.
- `purchases.csv`: 6,889 rows.
- `campaign.csv`, `content_calendar.csv`: not used (content calendar has 6 events every 45 days from day 30; noted for Learnings only).
- Label-window filter: 12,000 of 12,000 players survive (max signup_day is 179, so 179 + 55 = 234 <= 269; the filter is a no-op on this dataset but stays in the code as a guard).
- Never-engaged players (zero activity rows in lifetime days 0..27): 326 (2.7%); their churn rate is 0.752.
- Positive rate, all eligible players: **0.3293** (n = 12,000).
- Positive rate, excluding never-engaged: **0.3175** (n = 11,674).

## Design

Approach: one feature table per player built with pandas groupby from the first 28 lifetime days, one HistGradientBoostingClassifier with sklearn defaults, one stratified 70/15/15 split, scored once on test. No model comparison, no tuning.

Assumptions (all self-inferred, applied as "fast defaults"):

- Lifetime day = `day - signup_day`; asserted non-negative for every activity row (holds).
- Prediction point = lifetime day 28; feature window = lifetime days 0..27; label window = lifetime days 28..55 inclusive.
- Churn = zero activity rows in the label window. A single game on any day in the window means "not churned".
- Cleaning: missing activity aggregates filled with 0; `days_since_last_activity` for never-engaged players set to 28 (the full window), `first_active_day` set to 28, `last_active_day` set to -1; `win_rate` and `party_share` (undefined when games = 0) median-imputed. Nothing fancier.
- Features: active_days, total_games, total_wins, total_party_games, total_minutes, win_rate, party_share, days_since_last_activity (relative to day 28), last_active_day, first_active_day, active_days_last7, games_last7, n_purchases, total_spend, any_purchase, signup_day (numeric calendar cohort), one-hot of region / platform / acquisition_source. 25 columns total.
- Numerics standard-scaled (fit on train only). Scaling is irrelevant to a tree model but is applied as the stated default and would matter if the logistic-regression fallback were used.
- Split: stratified train/val/test 70/15/15 with random_state=42 (8,400 / 1,800 / 1,800). Random split by player, not by time; cohort leakage across calendar time is accepted for a baseline.
- Threshold chosen on validation by maximizing F1, then applied unchanged to test.
- Feature importance: permutation importance on test with scoring = average precision, 5 repeats.
- `_truth/players_truth.csv` read once, after evaluation, only for the grading-key sanity line.

## Implementation

Command:

```
cd /Users/alex/dev/sandbox/labs/ml-churn-1/monkey-mode && /Users/alex/dev/sandbox/.venv/bin/python baseline.py
```

`baseline.py`, as run:

```python
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
```

Full stdout of the run:

```
players=12,000 activity=748,811 purchases=6,889
activity day range: 0..269
eligible players (signup_day+55<=269): 12,000 of 12,000
never-engaged players (0 activity in days 0..27): 326 (2.7%); their churn rate: 0.752
positive rate (all eligible): 0.3293  n=12,000
positive rate (excluding never-engaged): 0.3175  n=11,674
feature matrix: (12000, 25)
split sizes train/val/test: 8400/1800/1800
val PR-AUC=0.7833 best-F1 threshold=0.4522 (val F1=0.7832)

=== TEST RESULTS ===
positive rate (test): 0.3294   PR-AUC random ref = 0.3294
PR-AUC: 0.7613   ROC-AUC: 0.8992
@thr=0.4522: precision=0.7069 recall=0.8988 F1=0.7914
success bar: PR-AUC>=2x pos rate (0.6589) -> True; ROC-AUC>=0.75 -> True; VERDICT: PASS

top-10 permutation importance (drop in test PR-AUC):
days_since_last_activity    0.3074
signup_day                  0.0439
party_share                 0.0179
total_wins                  0.0114
total_minutes               0.0105
last_active_day             0.0092
active_days_last7           0.0088
active_days                 0.0071
first_active_day            0.0048
total_spend                 0.0039

[grading-key check] label rate by _truth state_at_cutoff:
                  mean  size
state_at_cutoff             
active           0.060  4832
churned          0.601  4634
lapsed           0.346  2534

runtime: 4.6s
```

## Results

Test split (n = 1,800), one run, random_state = 42:

| Metric | Value |
|---|---|
| Positive rate (test) = PR-AUC random reference | 0.3294 |
| **PR-AUC (primary)** | **0.7613** |
| ROC-AUC | 0.8992 |
| Threshold (max-F1 on validation) | 0.4522 |
| Precision @ threshold | 0.7069 |
| Recall @ threshold | 0.8988 |
| F1 @ threshold | 0.7914 |
| Validation PR-AUC (for reference) | 0.7833 |

Verdict against the stated success bar:

- PR-AUC >= 2x positive rate: 0.7613 >= 0.6589 -> pass (2.31x random).
- ROC-AUC >= 0.75: 0.8992 >= 0.75 -> pass.
- **VERDICT: PASS.** The target is learnable with a trivial model.

Top-5 permutation importances (mean drop in test PR-AUC when the column is shuffled, 5 repeats):

| Feature | Drop in PR-AUC |
|---|---|
| days_since_last_activity | 0.3074 |
| signup_day | 0.0439 |
| party_share | 0.0179 |
| total_wins | 0.0114 |
| total_minutes | 0.0105 |

Runtime: 4.6 s end to end.

## Learnings

- **The target is learnable, and it is essentially a recency problem.** `days_since_last_activity` alone accounts for a 0.31 drop in PR-AUC when shuffled; the next feature is 7x smaller. A rule "churned if no activity in the last N days of the feature window" would capture most of the lift. Frequency and volume features (active_days, total_games, total_minutes) add little on top of recency.
- **Calendar cohort matters (signup_day is the second feature).** Churn rate varies with when a player signed up. Plausible causes in this dataset: the content calendar (events at days 30, 75, 120, 165, 210, 255 land in different lifetime days for different cohorts) and any generator-level cohort drift. A random player split lets the model exploit this; a time-based split would be the honest test of whether it generalizes to new cohorts.
- **Social play is protective.** `party_share` is the third feature; players who play a higher share of party games churn less, which is consistent with the `social` latent in the generator.
- **Purchases are weak signals.** Only 6,889 purchases across 12,000 players over 270 days; `total_spend` is 10th and `any_purchase` did not make the top 10. Spend is not a useful early-churn feature here at day 28.
- **Never-engaged players are a small, near-deterministic slice.** 326 players (2.7%) have no activity in their first 28 days; 75% of them are labeled churned. Keeping them shifts the positive rate from 0.3175 to 0.3293. They are trivially easy for the model and slightly inflate metrics; the operational question is whether the product wants to target them at all.
- **Precision/recall shape.** At the max-F1 threshold the model catches 90% of churners at 71% precision. The precision side is where the headroom is: about 3 in 10 flagged players would not have churned under this definition.
- **No data issues found.** No activity rows before signup, day ranges as documented, every player's label window is observable (max signup_day 179), no nulls in the raw files that reached the feature table.
- **Grading-key check (read-only, post-evaluation, `_truth/players_truth.csv`, not used as a feature):** label rate by `state_at_cutoff` is active 0.060 (n = 4,832), lapsed 0.346 (n = 2,534), churned 0.601 (n = 4,634). The ordering is right, but note that `_truth` cutoff is absolute day 180 (the campaign cutoff, per `_truth/params.csv`), not my lifetime day 28, so this is a directional check only, not label validation. That 40% of generator-"churned" players still show activity in lifetime days 28..55 says the generator's churn is a later-life state for many players, not something that has happened by day 55.

## Suggested Next Steps

Implications for the regular design flow (monkey-mode did not read or write `design/`, `prd/`, `modeling/`, `adr/`, or `spec/`):

1. **Revisit the label definition in the PRD.** "Zero activity in lifetime days 28..55" is a self-inferred choice. Given the recency dominance, a 28-day inactivity window is close to a tautology of "already inactive at day 28". Options worth deciding explicitly: a shorter feature window with a longer label horizon (e.g. features from days 0..13, label on 14..55), a label that requires a return-to-play rather than any activity, or defining churn as "no activity for 28 consecutive days at any point before day 90". The choice changes both the positive rate (0.33 here) and which features matter.
2. **Decide how to treat never-engaged players** (2.7%, 75% churn). Either exclude them and report on the engaged population, or keep them but route them to a separate "activation" treatment rather than a churn-save one.
3. **Use a time-based (cohort) split in V1 evaluation.** signup_day being the second feature is a warning that a random split overstates generalization to future cohorts. Hold out the latest signup cohorts as test.
4. **A V1 gradient-boosted model is a reasonable bet** but is not necessary for the first release: a recency rule plus a party-share tie-breaker would deliver most of the value. The design doc should state what the model has to beat (that rule), not just "random".
5. **Consider a multi-horizon or earlier prediction point.** If the business action is a retention nudge, predicting at day 28 with a window that is already mostly decided by recency may be too late. Compare prediction at day 7 and day 14 against the same label window and see how much PR-AUC is lost.
6. **Purchases can be deprioritized as features** for the day-28 problem; spend prediction is a separate task.
7. **Check the content-calendar interaction** before shipping: whether an event landing inside a cohort's label window mechanically lowers that cohort's churn rate, which would make signup_day a proxy for event timing rather than a real cohort effect.
