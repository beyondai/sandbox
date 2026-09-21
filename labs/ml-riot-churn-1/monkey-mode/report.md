# Monkey-Mode Fast Baseline: Player Lapse Prediction

Track: `ml-system-design-monkey-mode`. One-shot, autonomous fast baseline, independent of the separate `design/deep-dive.md` design track for this project.

## Requirements

All three resolved by the user (not self-inferred):

1. **Task + data** (answered by user): Predict 28-day lapse risk for recently-active players.
   - Data: `players.csv`, `activity.csv`, `campaign.csv` from the lifecycle dataset.
   - Cutoff day `c`. Population = players whose last activity day strictly before `c` falls in `[c-7, c)`.
   - Label = 1 ("lapsed") if the player has zero `activity.csv` rows with `day` in `[c, c+28)`; else 0.
   - Features and population built only from `activity.csv[day < c]` (no look-ahead).
   - Train cutoff `c=135` (labels from day 135-162); test cutoff `c=180` (labels from day 180-207).
   - At the test cutoff only, exclude players in `campaign.csv` with `treated=1` (comeback-offer campaign sent exactly on day 180). `treated=0` (control) players are kept.

2. **Primary metric** (answered by user): PR-AUC, plus precision/recall/F1 at threshold 0.5.

3. **Success bar** (answered by user): PR-AUC >= 0.30, treated as a soft target (derived from F2P churn-literature ROC-AUC ranges and the ~8.7% positive-rate floor, not a matching prior baseline), not a hard gate.

## Input

Real data read directly, no samples or truncation:

- `/Users/alex/dev/sandbox/data/riot-synthetic/synthetic-data/data/lifecycle/players.csv` - 12,000 rows
- `/Users/alex/dev/sandbox/data/riot-synthetic/synthetic-data/data/lifecycle/activity.csv` - 748,811 rows (day range 0-269)
- `/Users/alex/dev/sandbox/data/riot-synthetic/synthetic-data/data/lifecycle/campaign.csv` - 3,150 rows (1,580 treated / 1,570 control, all sent on day 180)
- `content_calendar.csv` and `purchases.csv` were not used (out of scope for this minimal feature set).

## Design

Fast defaults, applied directly to this problem:

- **Cleaning**: `region` (~29% null in `players.csv`) filled with the literal string `"unknown"` as its own category, not dropped or guessed. No other nulls in the columns used.
- **Population/labels**: built with a single `build_dataset(c, exclude_treated)` function reused for both cutoffs, to keep the train/test construction logic identical and avoid asymmetric bugs. `exclude_treated=True` only at `c=180`.
- **Features**, all computed from `activity.csv[day < c]`:
  - `active_days_28d`, `games_28d`, `wins_28d`, `party_games_28d`, `minutes_28d` (trailing-28-day sums/counts from `[c-28, c)`)
  - `win_rate_28d` = wins/games, `party_share_28d` = party_games/games (0 when games_28d=0)
  - `days_since_last_active` = c - last pre-cutoff active day
  - `tenure` = c - signup_day
  - `region`, `platform`, `acquisition_source` - one-hot encoded
- Numeric features standard-scaled, categoricals one-hot encoded, remaining numeric nulls median-imputed (guard for an edge case that did not occur in practice).
- **Model**: single `LogisticRegression(class_weight="balanced")` in an sklearn `Pipeline` with `ColumnTransformer`. No tuning, one fit.
- **Sanity check** (explicitly required by task): asserted computed churn rate is strictly between 2% and 50% for both train and test populations, to catch the exact look-ahead-leak bug called out in the task (rows with `day >= c` leaking into the "last activity day" computation, which forces churn to ~100%). Both cutoffs passed at ~8%, matching the expected imbalanced-but-plausible rate.

## Implementation

Full script: `/Users/alex/dev/sandbox/labs/ml-riot-churn-1/monkey-mode/baseline.py`. Run via `uv run python3 baseline.py`. Key logic (population/label construction, the part most prone to the look-ahead bug):

```python
def build_dataset(c, exclude_treated=False):
    hist = activity[activity["day"] < c]                        # features/population: day < c only
    future = activity[(activity["day"] >= c) & (activity["day"] < c + 28)]  # labels only

    last_day = hist.groupby("player_id")["day"].max().rename("last_activity_day")
    pop = last_day[(last_day >= c - 7) & (last_day < c)].index   # active in trailing week

    pop_df = pd.DataFrame({"player_id": pop})
    if exclude_treated:
        treated_ids = set(campaign.loc[campaign["treated"] == 1, "player_id"])
        pop_df = pop_df[~pop_df["player_id"].isin(treated_ids)]

    future_players = set(future["player_id"].unique())
    pop_df["label"] = (~pop_df["player_id"].isin(future_players)).astype(int)
    # ... trailing-28d feature aggregation, then merge with players.csv
    return df, numeric_cols
```

Model:

```python
preprocessor = ColumnTransformer([
    ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
])
model = Pipeline([("prep", preprocessor), ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))])
model.fit(X_train, y_train)
```

Raw run output is captured in `/Users/alex/dev/sandbox/labs/ml-riot-churn-1/monkey-mode/results.json`.

## Results

Actual output from running the script:

| Population | n | Positive rate |
|---|---|---|
| Train (cutoff c=135) | 4,954 | 8.20% |
| Test (cutoff c=180, treated excluded) | 4,675 | 8.68% |

**Sanity check**: passed. Churn rates landed at ~8-9%, nowhere near the degenerate 0%/100% that the look-ahead-leak bug would produce.

| Metric | Value | vs. bar |
|---|---|---|
| **PR-AUC** | **0.4774** | >= 0.30 bar -> **MET** (comfortably, ~1.6x the bar) |
| Precision @0.5 | 0.3367 | |
| Recall @0.5 | 0.7438 | |
| F1 @0.5 | 0.4635 | |

Note on threshold 0.5: `class_weight="balanced"` reweights the loss during training but `predict_proba` at 0.5 still yields a high-recall, lower-precision operating point here (predicted positive rate 19.2% vs. actual 8.7% positive rate) - expected behavior for a balanced-weighted classifier on an imbalanced set at an un-shifted threshold, not a bug. PR-AUC (threshold-independent) is the metric the success bar is actually defined against.

## Learnings

- **The target is learnable with a trivial feature set.** A single logistic regression on 9 hand-built features clears the soft PR-AUC bar by a wide margin (0.48 vs 0.30), meaning trailing-28-day engagement volume, win rate, party-play share, and recency carry real signal for who lapses in the next 28 days. That's a meaningfully positive signal for the "regular" design track, not just a pass/fail checkbox.
- **The look-ahead sanity check is not paranoia** - the task explicitly flagged that an earlier pass at this exact problem hit this bug and silently forced churn to 100%. Building population and features from a single `hist = activity[day < c]` slice (never touching `future` for anything but labels) made the bug structurally hard to reintroduce, and the assertion would have caught it immediately if it had crept back in.
- **Independent cross-check**: computed train/test population sizes and positive rates (4,954/8.20%, 4,675/8.68%) landed exactly on the same numbers independently reported in this project's `design/deep-dive.md` (drafted separately, not read until after this baseline ran) - good evidence the population/label definition is unambiguous and both passes implemented it the same way.
- **Recall vs. precision tradeoff is real at the default threshold**: at 0.5, the model flags roughly 1-in-5 test players as at-risk to catch 3-in-4 actual lapsers, at the cost of precision near 34%. Whether that's the right operating point depends entirely on the downstream retention-offer cost/reach tradeoff, which this baseline deliberately doesn't decide.
- **campaign.csv exclusion mattered for population size but not verified for selection-bias direction**: excluding the 1,580 treated players at test time is straightforward set-membership filtering; it wasn't compared against an unfiltered run since that wasn't asked for. The main risk it addresses is contaminated labels among treated players in the label window, which this baseline avoids as instructed.

## Suggested Next Steps

For the separate `design/deep-dive.md` track (read only to phrase this compatibly, not modified):

- The deep-dive's **V0 baseline** (`days_since_last_active` alone) is worth running for real now that this fast pass shows the richer feature set clears the bar comfortably - it would quantify exactly how much lift the other 8 features add over recency alone, which the deep-dive currently treats as an assumption ("establishes the floor the real model has to beat").
- The deep-dive's **V1 from-scratch logistic regression** should reference-check against numbers very close to this run's sklearn baseline (PR-AUC ~0.48, same class-weighted-log-loss formulation) - if V1 lands far below that, it's a from-scratch implementation bug, not an inherent task difficulty limit, since this baseline already shows the task is learnable at that level with the same feature family.
- The deep-dive's **V2 hazard model / HistGradientBoosting ceiling check** now has a concrete number to beat: if the more flexible model doesn't clear PR-AUC meaningfully above ~0.48, that's evidence the trailing-28-day snapshot features are close to sufficient and the extra complexity (censoring-aware hazard formulation, reshaping to one row per active-period) may not be worth it for the lapse model specifically - worth checking before investing in the reshape.
- The precision/recall tradeoff observed here (74% recall / 34% precision at threshold 0.5) is a concrete input for the deep-dive's not-yet-written delivery/rollout section: a retention-offer program sized for ~19% of the recently-active population should be budgeted against this baseline's operating point, then adjusted once the real threshold-selection pass happens.
