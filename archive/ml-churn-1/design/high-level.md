# High-level design: player churn at lifetime day 28 (60-day window)

- Project: `labs/ml-churn-1/`
- Mode: Quick POC - each item below is the most likely answer in one pass;
  anything not already settled in `prd/churn.md` is flagged **(assumption)**.
- Inputs: `prd/churn.md` (as updated 2026-09-20: 60-day window, Brier score), `monkey-mode/report.md` (baseline numbers only)

## ML framing

**"Figure out who's staying and who is leaving" becomes: for every player who
reaches lifetime day 28, predict the probability that they log zero activity
in lifetime days 28-87 (60 days) - binary classification, scored in a daily batch, used
to rank players for retention outreach.**

This folder builds: the day-28 early-lifecycle churn classifier (one model).

| | |
|---|---|
| Prediction target | P(churned) per player, a probability in [0, 1] used as a ranking score plus a threshold |
| Label + horizon | churned = 1 if zero activity rows in lifetime days 28-87 inclusive (60-day inactivity window), else 0. Horizon: 60 days after the prediction point. Set in PRD, option (a) with the window widened to 60 days. |
| Scoring population + cadence | Every player whose lifetime day 28 is today (absolute day = `signup_day + 28`). Daily batch. Training population: all players with `signup_day + 87 <= last observed day` so the full label window is observable (12,000 in this data; positive rate 0.30). |
| Unit of prediction | One row = one (player, lifetime-day-28) snapshot. Each player appears exactly once. |
| Features window | Only data with absolute day < `signup_day + 28`, plus static `players.csv` attributes. Lifetime-relative, so cohorts are comparable. |
| Exclusions / contamination | `_truth/` never enters features or labels. `campaign.csv` (day-180 offer) is out of scope but can contaminate the label: the offer lands at absolute day 180, which falls inside the label window (days `signup_day+28` to `signup_day+87`) for players with `93 <= signup_day <= 152`. **(assumption)** These players are kept, and the data step must check whether `treated=1` players in that band have a lower in-window churn rate than `treated=0`; if so, exclude treated players with an in-window send day (a few hundred at most, `campaign.csv` has ~3,150 rows). Never-engaged players (326, zero activity in days 0-27) are kept and reported separately. Content-calendar events (every 45 days from day 30) land in different lifetime days per cohort - a known confounder, handled by the cohort split, not excluded. |
| Primary metric | PR-AUC vs. positive rate 0.30, cohort holdout, beat the recency rule - see `prd/churn.md`, Metrics - offline. |

## Architecture

Two paths. Nothing in this project is request/response: "online inference"
here is a daily batch that produces a scored list, consumed by CRM tooling.

### Inference (daily batch) **(assumption: batch shape, table names)**

```
 [game activity log]  [purchase log]  [player master]
   activity.csv         purchases.csv   players.csv
        |                    |               |
        v                    v               v
 +-------------------------------------------------+
 | 1. select cohort: players with                  |
 |    signup_day + 28 == today                     |
 +-------------------------------------------------+
        |
        v
 +-------------------------------------------------+
 | 2. feature build (same code as training):       |
 |    per-player aggregates over lifetime days     |
 |    0-27: recency, frequency, intensity, spend,  |
 |    static one-hots                              |
 +-------------------------------------------------+
        |
        v
 +-------------------------------------------------+
 | 3. score: load model artifact (models/churn.pkl)|
 |    -> p_churn per player                        |
 +-------------------------------------------------+
        |
        v
 +-------------------------------------------------+
 | 4. rank + threshold: sort by p_churn, apply     |
 |    threshold (val-tuned) and top-20% contact cap|
 +-------------------------------------------------+
        |
        v
   scores table (player_id, score_day, p_churn, flagged)
        |
        v
   CRM targeting list  (out of scope: which offer)
```

Budget: whole batch within 2 hours (PRD); the POC does it in seconds on
12,000 players with pandas.

### Training (offline, retrained by hand for the POC) **(assumption: cadence)**

```
 SOURCES (data/riot-synthetic/synthetic-data/data/lifecycle/)
   players.csv     player_id, signup_day, region, platform, acquisition_source
   activity.csv    player_id, day, games, wins, party_games, minutes
   purchases.csv   player_id, day, amount_usd, item_type, offer_price
   (not used: campaign.csv, content_calendar.csv, _truth/)
        |
        v
 +-------------------------------------------------+
 | build_dataset: lifetime_day = day - signup_day  |
 |   keep players with signup_day + 87 <= max day  |
 |   label  = no activity in lifetime days 28-87   |
 |   features = aggregates over lifetime days 0-27 |
 |   -> one row per player                         |
 +-------------------------------------------------+
        |
        v
 +-------------------------------------------------+
 | split by signup cohort (PRD): oldest cohorts    |
 |   train, middle val, newest cohorts test        |
 +-------------------------------------------------+
        |
        v
 +-------------------------------------------------+
 | train: recency-rule baseline + gradient-boosted |
 |   trees; threshold tuned on val                 |
 +-------------------------------------------------+
        |
        v
 +-------------------------------------------------+
 | evaluate on newest-cohort test: PR-AUC, ROC-AUC,|
 |   F1 / precision / recall at threshold,         |
 |   precision@top-20%, Brier score               |
 +-------------------------------------------------+
        |
        v
   model artifact + metrics json  ->  picked up by the inference batch
```

Retraining: manual in the POC; **(assumption)** monthly in production, since
the label needs 87 days of history and cohort drift showed up as the #2
feature in the baseline.

## Phasing

| Phase | Features shipped | Model class | Timeline | Headcount |
|---|---|---|---|---|
| **V0 - crawl** (done: `monkey-mode/`, 28-day window, so not comparable to V1 numbers) | 25 aggregates over lifetime days 0-27: active days, games, wins, minutes, win rate, party share, days since last activity, last-7-day activity, purchases, spend, signup_day, static one-hots | Recency rule (`days_since_last_activity`) as the bar; one default HistGradientBoosting, random split. PR-AUC 0.76 / ROC-AUC 0.90 | Done, 5 s run | 0.1 FTE |
| **V1 - walk** (this POC) | Same feature set plus: weekly activity trend (week 4 vs. week 1), sessions-per-active-day, days since last purchase, streak length; cohort holdout split; threshold + top-20% cap | Gradient-boosted trees, light tuning; logistic regression as an interpretable check. Must beat the recency rule on the newest-cohort test | ~1 hour of work in the `ml-modeling-*` chain, or 1 day if done by hand | 1 person (you) |
| **V2 - run** **(assumption)** | Content-calendar features (days to next event at day 28), social features (party-partner retention), sequence features over the 28 days | Same model class with a proper daily-batch job, monthly retrain, monitoring on score drift and cohort positive rate; optionally a sequence model if V1 plateaus | 2-4 weeks | 1 ML engineer + 0.5 data engineer for the pipeline |

## Fork

Next: either `ml-system-design-deep-dive churn poc` (paper) or
`ml-modeling-data` (hands-on; synthesizes `spec/churn.md` from this file +
the PRD). Both land at `ml-system-design-delivery`.
