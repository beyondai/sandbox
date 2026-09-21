# Monkey-mode baseline: riot-synthetic churn prediction

## Requirements

- **Task + data (user-answered)**: Binary classification - did a player stay
  (active) or leave (lapsed/churned) by day 180? Data root:
  `/Users/alex/dev/sandbox/data/riot-synthetic/synthetic-data/data/lifecycle/`,
  using `players.csv`, `activity.csv` (aggregated pre-cutoff), and
  `purchases.csv` (aggregated pre-cutoff). `campaign.csv` and
  `content_calendar.csv` excluded. Label from
  `_truth/players_truth.csv`'s `state_at_cutoff`, collapsed to active=0,
  lapsed/churned=1, using only that one column from the truth file (its
  other columns are hidden generative parameters, not observable features).
- **Primary metric (user-answered)**: Both F1 and ROC-AUC, both reported.
- **Success bar (user-answered method: "look one up")**: a web-searched,
  cited benchmark, translated into a soft F1/ROC-AUC target, with an
  explicit check for population mismatch (see Results).
- **Self-inferred - exact feature list**: total/mean games, wins, minutes,
  party games, active-day count, last-active day, days-since-last-activity,
  first-half-vs-second-half activity trend (from `activity.csv`); total
  spend, purchase count, distinct item types, offer-purchase rate (from
  `purchases.csv`); signup_day, region, platform, acquisition_source (from
  `players.csv`).
- **Self-inferred - null handling nuance**: the fast default says
  "drop or median-impute nulls." For players with zero rows in
  `activity.csv`/`purchases.csv` before the cutoff, a merge produces NaN
  aggregates - these were filled with 0 (no activity/spend happened), not
  the median, since median-imputing "typical" activity for a player who
  never appears in the log would fabricate a false signal. `region` has
  genuine missingness (see Input) and was filled with an explicit
  "Unknown" category rather than dropped or mode-imputed, since dropping
  29% of rows would throw away real data and the missingness itself may be
  informative.
- **Self-inferred - model**: RandomForestClassifier (300 trees, max_depth 8,
  min_samples_leaf 5), one of the two fast-default options ("a single small
  tree ensemble"), chosen over logistic regression so a feature-importance
  read-out is available for the Learnings section.
- **Self-inferred - split**: 80/20 train/test, stratified on the binary
  label, `random_state=42`.

## Input

- **Paths used**: `players.csv` (12,000 rows, 1 row per player, no
  duplicate `player_id`), `activity.csv` (748,811 rows total; 504,296 rows
  with `day < 180` used for features), `purchases.csv` (6,889 rows total;
  4,256 rows with `day < 180` used), `_truth/players_truth.csv` (12,000
  rows, label only). `_truth/params.csv` confirms `cutoff_day = 180`,
  verified before coding via `head`/`wc -l` on every file.
- **Class balance**: `state_at_cutoff` = active: 4,832; churned: 4,634;
  lapsed: 2,534. Collapsed to binary: stayed (0) = 4,832 (40.3%), left (1)
  = 7,168 (59.7%). Mild imbalance toward the positive ("left") class, not
  severe enough to require resampling for a fast baseline.
- **Nulls found**: `players.region` has 3,521/12,000 nulls (29.3%) - 
  handled as its own "Unknown" category (see Requirements). No nulls in
  `activity.csv`, `purchases.csv`, or the truth file. `signup_day` in
  `players.csv` is fully populated (range 0-179); a median-impute guard was
  left in the code defensively but never triggers.
- **Leakage exclusions applied**:
  - `campaign.csv` (3,150 rows): a day-180 re-engagement offer targeted at
  players already identified as lapsing. Any column derived from it
  would leak the label by construction. Excluded entirely.
  - `content_calendar.csv`: a global, non-per-player signal (6 rows of
  calendar-wide events). Not usable as a per-player feature; skipped for
  a fast baseline.
  - `_truth/players_truth.csv` columns other than `state_at_cutoff`
  (`social`, `engage`, `payer_initial`, `payer_at_cutoff`, `spend_rate`,
  `amount_mu`, `days_lapsed_at_cutoff`): these are the hidden generative
  parameters that produced the synthetic activity/purchase logs, not
  observable signals a real system would have - using them as features
  would be direct label leakage. Excluded.
  - `activity.csv` / `purchases.csv`: filtered to `day < 180` before
  aggregating, so no post-cutoff behavior enters the features.

## Design

- **Cleaning**: per fast defaults, zero-fill for "no rows before cutoff"
  aggregates, explicit "Unknown" category for genuinely missing `region`,
  defensive median-impute for `signup_day` (see Requirements for the
  reasoning behind deviating from a blind median-impute-everything rule).
- **Features**: standard-scaled numeric features (22: signup_day; 11
  activity aggregates including win_rate/party_rate; last_active_day and
  days_since_last_activity; 4 purchase aggregates) plus one-hot-encoded
  low-cardinality categoricals (region: 5 levels incl. Unknown; platform: 2
  levels; acquisition_source: 3 levels), built with a single
  `ColumnTransformer` inside a `Pipeline` so train/test preprocessing stays
  consistent.
- **Model**: one `RandomForestClassifier`, trained once, no
  hyperparameter search - this is a baseline, not a model comparison.
- **Eval**: single stratified 80/20 train/test split, F1 and ROC-AUC
  computed on the held-out 20% only.

## Implementation

Full script: `/Users/alex/dev/sandbox/labs/ml-riot-churn-1/monkey-mode/baseline.py`.
Key excerpts (feature aggregation and model):

```python
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
    first_half_minutes=("minutes", "sum"), first_half_games=("games", "sum")
)
second_half = act[act["day"] >= CUTOFF_DAY / 2].groupby("player_id").agg(
    second_half_minutes=("minutes", "sum"), second_half_games=("games", "sum")
)
# ... trend, win_rate, party_rate, days_since_last_activity derived from
# these, then joined onto players.csv and purchases aggregates.

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

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
)
model.fit(X_train, y_train)
```

Actually run with the project venv:
`/Users/alex/dev/sandbox/labs/ml-riot-churn-1/monkey-mode/.venv`
(pandas 3.0.6, scikit-learn 1.9.1, numpy 2.5.3 - the system Python had none
of these installed, so a local venv was created; see
`SKILL-IMPROVEMENTS.md`). Full console output captured in
`run_output.txt` in this folder.

## Results

Held-out test set (n=2,400, stratified 20% split):

- **F1**: 0.9683
- **ROC-AUC**: 0.9899

Per-class detail: precision/recall/F1 of 0.94/0.97/0.95 for "stayed" and
0.98/0.96/0.97 for "left" (support 966 / 1,434).

**Benchmark search and comparison**:

- Primary source: Sulman Khan, "Predicting Customer Churn in World of
  Warcraft," arXiv:2006.15735 (2020),
  https://arxiv.org/abs/2006.15735 - an existing subscriber base (not new
  installs), aggregated playing-behavior features, predicting churn
  6 months out with logistic regression / SVM / KNN / random forest. Best
  model: 96% ROC-AUC. No F1 reported. This is the closest population match
  available: an established player base, months-ahead binary churn from
  aggregated behavioral features - structurally the same setup as this
  task.
- Secondary source (population mismatch, flagged explicitly): Mustač,
  Bačić, Skorin-Kapov, and Sužnjević, "Predicting Player Churn of a
  Free-to-Play Mobile Video Game Using Supervised Machine Learning,"
  Applied Sciences 12(6):2795, MDPI (2022),
  https://www.mdpi.com/2076-3417/12/6/2795 - best reported F1 is 0.78
  (logistic regression), but this is measured on 1-7-day post-install
  feature windows predicting 1-7-day-ahead early churn. That is a
  new-install/trial-user population, not the broader existing player base
  lapsing by a fixed day-180 cutoff that this task addresses - per the
  brief's own caution, this number is NOT adopted as directly equivalent;
  it is cited only as the best available F1 reference point since no
  closer-population source reported F1.
- **Soft target translated from these two sources**: ROC-AUC roughly
  0.85-0.96 (anchored on the WoW paper, discounted slightly for a
  much-simpler feature set and no model tuning); F1 roughly 0.65-0.78
  (anchored loosely on the mobile-game paper, with the population-mismatch
  caveat above, and general expectation that F1 near the top of that range
  requires either an easier task or heavier modeling than a fast
  baseline).
- **Comparison**: the baseline's F1 (0.9683) and ROC-AUC (0.9899) both
  exceed the top of the soft-target range from either source. The baseline
  clearly meets, and substantially beats, the success bar.

## Learnings

- **The task, as posed, is very easy for a model** - likely too easy to be
  representative of a real deployed scenario. Feature importances show
  `last_active_day` (0.343) and `days_since_last_activity` (0.301) alone
  account for roughly two-thirds of total importance; `second_half_minutes`
  and `second_half_games` (recent-window activity) add most of the rest.
  This makes sense mechanically: in this dataset, a player who has
  "lapsed" or "churned" by day 180 has, almost by definition, stopped
  generating activity rows well before day 180, so "how recently did they
  last play, measured right up to the cutoff" is close to a direct proxy
  for the label rather than a predictive signal learned ahead of the
  outcome. A real product would face the same shortcut if it computed
  features all the way up to the outcome date rather than an earlier
  observation date.
- **Class balance is mild** (40/60), not a modeling obstacle at this
  baseline stage.
- **A real data-quality wrinkle**: `players.region` is missing for 29% of
  players. It wasn't a strong feature either way in this run (not in the
  top 10 importances), but it is a preprocessing decision (drop vs. impute
  vs. "Unknown" category) that a real design pass should make deliberately
  rather than by fast-mode default.
- **Leakage risk was real, not hypothetical**: `campaign.csv` is targeted
  at players already flagged as lapsing at day 180 - including any
  campaign-derived feature (even "was this player offered the campaign")
  would have leaked the label almost perfectly, and the truth file's extra
  columns (`payer_at_cutoff`, `days_lapsed_at_cutoff`, etc.) are literally
  the generative parameters behind the label. Both exclusions mattered
  more than any feature-engineering choice made here.

## Suggested Next Steps

- Recency-based features (last-active-day, days-since-last-activity,
  recent-window activity trend) dominate here. If the regular design flow
  frames this as "predict lapse using data available at prediction time,"
  it should pick a prediction date meaningfully earlier than the outcome
  cutoff (e.g., score at day 120 using only data through day 90-100 to
  predict day-180 state) - otherwise a V1 model risks learning the same
  near-tautological "haven't played recently = already gone" shortcut this
  baseline found, which is far less useful for early intervention.
- Binary lapse-vs-active framing (collapsing lapsed+churned) looks entirely
  workable from this run - the model separates the two classes cleanly, so
  there's no evidence the 3-class distinction (active/lapsed/churned) is
  necessary for a first model; it may still be worth keeping as a
  post-hoc breakdown of the same binary model's errors rather than a
  modeling target in its own right.
- Purchase-derived features and most categorical features (region,
  platform, acquisition_source) contributed little to this baseline's
  importance ranking. Before investing engineering effort there in a
  fuller design, it's worth checking whether that's because they carry
  real signal that recency features simply overshadow (multicollinearity
  with the dominant recency signal), or because they genuinely don't
  matter for this label.
- Given how high both metrics already are on the "easy" framing, the more
  valuable offline evaluation for a real design is likely an earlier
  prediction-date variant (see above) - its harder, more realistic
  F1/ROC-AUC would be a more useful design signal than this baseline's
  near-ceiling numbers.
