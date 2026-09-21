# Design Deep Dive: Player Churn and Revival

Builds on `prd/player-churn-and-revival.md` and `design/high-level.md`
(binary classification, two separate models, lapse H=28 / revival H=14,
offline-batch-only architecture, ADR `0001` for the two-models decision).
This supersedes the earlier out-of-order draft at
`labs/ml-riot-churn-1/design/deep-dive.md`, which used a 28-day horizon for
both models and predates the PRD — do not reuse its revival numbers.

All numbers below are computed directly from the CSVs, never from
`_truth/` or the prep doc's spoilers section.

## Data

**Real-time inference sources:** not applicable — per the PRD, this is
offline batch scoring only, no live-serving system in scope.

**Batch training sources:**
- `players.csv` — 12,000 players. `signup_day`, `region` (EUW/BR/KR/LATAM,
  **29.3% null** — kept as an explicit "unknown" category, not imputed or
  dropped), `platform` (pc 80.4% / mobile 19.6%), `acquisition_source`
  (organic 50.1% / paid_ads 29.7% / friend_referral 20.2%).
- `activity.csv` — 748,811 rows, one row per player-day actually played,
  days 0-269. 11,771 of 12,000 players have at least one row (229 never
  play at all and fall outside both models' populations).
- `content_calendar.csv` — 6 known event-start days (30/75/120/165/210/255),
  usable as a feature per the high-level design's revival-model rationale.
- `campaign.csv` — not a feature source. Used only to exclude
  campaign-treated players from the test-cutoff evaluation population.
- `purchases.csv`, `_truth/` — not used, per PRD scope (LTV and grading key
  respectively, both explicitly out of scope).

**New data engineering:** `activity.csv` is sparse (one row per day actually
played, not one row per day per player), so every feature below is derived
by grouping on `player_id` and windowing on `day` — none of it exists as a
column already. The two models need different window shapes: the lapse
model needs a trailing window (last 28 days before cutoff), the revival
model needs lifetime-to-date aggregates (a lapsed player's trailing-28-days
is mostly empty by construction, so a trailing window is the wrong shape
for that population).

## Features

Cutoff `c`: all features built only from `activity.csv[day < c]` — verified
against the earlier look-ahead-leak bug (see `ml-riot-churn-1`'s deep-dive
for how that was caught) by checking the resulting class balance is nowhere
near 0%/100% before trusting it.

**Lapse model** — population: last pre-cutoff active day in `[c-7, c)`.
- `active_days_28`, `total_games_28`, `total_minutes_28`, `win_rate_28`,
  `recent_loss_rate_7`, `party_share_28`, `avg_minutes_per_active_day_28`.
- `tenure_days` (c - signup_day), `days_since_last_active`.
- `days_to_nearest_content_event`.
- `region` (with "unknown" level), `platform`, `acquisition_source`.

**Revival model** — population: signed up before `c-7`, and last pre-cutoff
active day more than 7 days before `c` (or never played pre-cutoff).
- `days_since_last_active`, `tenure_at_lapse`, `lifetime_active_days`,
  `lifetime_games`, `lifetime_avg_minutes_per_session`,
  `lifetime_party_share`.
- `days_to_nearest_content_event` — the one feature that meaningfully
  differentiates this model from a generic recency heuristic.
- `region`, `platform`, `acquisition_source`.

## Models

Same phase structure as `design/high-level.md`'s V0/V1/V2, expanded with
the actual tradeoff reasoning:

| Phase | Model | Why |
|---|---|---|
| V0 | `days_since_last_active` alone, thresholded/ranked | No training; the floor both real models have to beat. Already run independently via monkey-mode (`ml-riot-churn-1/monkey-mode/`, PR-AUC 0.477 for a full logistic model, not V0 itself — a useful ceiling reference even though it predates this project). |
| V1 (primary) | Logistic regression, L2-regularized, from scratch (gradient descent) | Interpretable coefficients live-ops can act on; matches the PRD's "focus on ML model performance" framing without needing a black box. |
| V2 (stretch, lapse only) | Discrete-time hazard model (one row per player-active-period) | Handles censoring correctly and uses time-varying covariates instead of a single snapshot. Not required to close out the project. |
| Reference only | `sklearn.linear_model.LogisticRegression` with matching L2 penalty | Correctness check for V1's from-scratch coefficients, not a candidate to ship. |

The revival model reuses the same V0→V1 structure; V2's hazard reformulation
is lapse-only (a "time since lapse until return" hazard is a valid
extension but out of scope per `design/high-level.md`'s phasing).

## Training

**Labels**, both models, features strictly `day < c`, labels strictly
`day >= c`:
- Lapse (H=28): 1 if zero `activity.csv` rows in `[c, c+28)`.
- Revival (H=14): 1 if any `activity.csv` row in `[c, c+14)`.

**Backtesting cutoffs:** train `c=135`, test `c=180` — chosen so
`c_train + H ≤ c_test` holds for both horizons (135+28=163 ≤ 180 for lapse;
135+14=149 ≤ 180 for revival), and both cutoffs sit near a
`content_calendar` boundary rather than mid-event.

**Campaign contamination:** only players with `campaign.treated==1` are
excluded from the `c=180` evaluation population (control-arm players
received no intervention, so they're left in). Computed class balance:

| Population | n | Positive rate |
|---|---|---|
| Lapse, train c=135 (H=28) | 4,954 | 8.20% |
| Lapse, test c=180 (H=28, treated excluded) | 4,675 | 8.68% |
| Revival, train c=135 (H=14) | 5,181 | 3.65% |
| Revival, test c=180 (H=14, treated excluded) | 5,719 | 2.59% |

Note the revival rate roughly halved versus the earlier (superseded) H=28
draft's 5.21%/4.04% — expected, since fewer players return within a
tighter 14-day window. This makes the revival task more imbalanced than
originally scoped, which raises the stakes on the class-weighting choice
below.

**Sampling / class imbalance:** class-weighted logistic regression
(inverse class frequency), consistent with the high-level design and the
PRD's PR-AUC-primary framing. Given the revival task's imbalance is now
closer to 2.6-3.7% than the earlier 4-5% estimate, watch its PR-AUC
floor (random-classifier PR-AUC ≈ the positive rate itself) when judging
whether V1 clears a meaningful bar — a smaller floor makes a given PR-AUC
number look better without necessarily being more useful.

**Loss function:** weighted binary cross-entropy + L2 penalty (intercept
excluded from the penalty).

**Training algorithm:** batch gradient descent, reference-checked against
`sklearn.linear_model.LogisticRegression(penalty="l2", class_weight="balanced")`
on the same feature matrix.

**Evaluation population, restated:** report metrics only on each model's
own task population — never on "all 12,000 players," where near-term
activity looks artificially predictable because most players are simply
continuing what they were already doing.
