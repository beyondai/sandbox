# Riot Churn - High-level Design

Mode: Quick POC - each item below is a one-pass draft, assumptions flagged
inline. Review and override any of it before this becomes the fork point.

## ML framing

**One sentence**: Predict, for each currently active player, the probability
they will lapse or churn within the next 60 days, so live-ops can prioritize
proactive outreach ahead of natural drift.

This folder builds: one binary player-lapse/churn risk classifier (v0). Per
the PRD's scope, 3-class and uplift/causal framing are separate, later
efforts, not this model.

- **Prediction target**: binary churn-risk - 0 = stays active, 1 =
  lapses/churns - within a fixed forward-looking horizon.
- **Label definition and horizon** *(assumption)*: horizon = 60 days forward
  from the scoring date. Label is the player's observed state at that
  horizon (active vs. lapsed/churned), the same active-vs-left collapse used
  in the PRD and in the synthetic dataset's `state_at_cutoff` truth column.
- **Scoring population and cadence** *(assumption)*: all players active in
  the trailing 30 days as of the scoring date, scored weekly in a batch job.
- **Unit of prediction**: one row = one player, as of a given scoring date,
  with feature aggregates computed over a trailing window (e.g. 30/60/90
  days) ending at that date.
- **Known exclusions / contamination** *(assumption)*: brand-new players
  still in an onboarding grace period (e.g. first 14 days - a distinct
  cohort covered by the separate `newplayer` dataset, not this model) are
  excluded from scoring; players currently inside an active comeback-offer
  window (`campaign.csv`) are excluded from label construction during
  training, since the campaign's own effect would contaminate what
  "churned" means for them.

Primary offline metric stays in the PRD (F1 / ROC-AUC / precision@k);
referenced here, not restated.

## Architecture

Two separate paths - the batch scoring ("online"/serving) path that produces
scores consumed downstream, and the offline training path that produces the
model. This project has no real-time request/response path (see PRD
non-functional requirements: batch only for v0).

### Serving path (batch scoring, weekly)

```
+----------------+   +----------------+   +----------------+
| players table  |   | activity table |   | purchases table |
| (profile,      |   | (daily rows:   |   | (daily rows:    |
|  signup, geo)  |   |  games, wins,  |   |  amount, item)  |
+-------+--------+   |  minutes)      |   +--------+--------+
        |            +-------+--------+            |
        |                    |                      |
        +---------+----------+----------+-----------+
                   |
                   v
        +--------------------------+
        | feature builder            |
        | (trailing 30/60/90d agg,   |
        |  recency, RFM-style spend) |
        +-------------+--------------+
                       |
                       v
        +--------------------------+
        | churn-risk model            |
        | (batch scoring job, weekly) |
        +-------------+--------------+
                       |
                       v
        +--------------------------+
        | risk_score table             |
        | (player_id, score, as_of)    |
        +-------------+--------------+
                       |
                       v
        +--------------------------+
        | existing live-ops             |
        | comeback-campaign targeting   |
        | (campaign.csv mechanism)      |
        +--------------------------+
```

### Offline training path

```
+----------------+   +----------------+   +----------------+
| players table  |   | activity table |   | purchases table |
+-------+--------+   +-------+--------+   +--------+--------+
        |                    |                      |
        +---------+----------+----------+-----------+
                   |
                   v
        +--------------------------+
        | feature engineering          |
        | (same builder as serving,    |
        |  point-in-time correct)      |
        +-------------+--------------+
                       |
                       v
        +--------------------------+       +----------------------------+
        | label construction           |<------| historical outcome          |
        | (active vs. lapsed/churned   |       | (observed state at horizon, |
        |  at horizon)                  |       |  excludes campaign-window   |
        +-------------+--------------+       |  players - see exclusions)  |
                       |                       +----------------------------+
                       v
        +--------------------------+
        | train/eval split +           |
        | model training                |
        | (logistic / small GBM)        |
        +-------------+--------------+
                       |
                       v
        +--------------------------+
        | offline eval report           |
        | (F1, ROC-AUC, precision@k)    |
        +-------------+--------------+
                       |
                       v
        +--------------------------+
        | model registry                |
        +--------------------------+
```

## Phasing

**V0 - crawl**
- Features: recency/frequency activity aggregates (days since last play,
  sessions in trailing 30d), basic monetization (total spend, purchase
  count), static profile (region, platform, acquisition_source).
- Model class: baseline - logistic regression or a single small tree
  ensemble, matching the monkey-mode baseline already run for this project.
- Timeline *(assumption)*: 2-3 weeks.
- Headcount *(assumption)*: 1 ML engineer + part-time support from a data
  analyst partnering with live-ops to validate the risk list makes sense.

**V1 - walk**
- Features: richer behavioral trend features (activity deceleration,
  win-rate trend, party-play ratio), RFM-style purchase recency/frequency/
  monetary features, proximity to `content_calendar.csv` events.
- Model class: tuned gradient-boosted trees (XGBoost/LightGBM) with proper
  cross-validation and hyperparameter search, calibrated probabilities so
  precision@k is meaningful for campaign targeting.
- Timeline *(assumption)*: 4-6 weeks after V0 is validated in production.
- Headcount *(assumption)*: 1-2 ML engineers, plus data engineering support
  to productionize the trailing-window feature pipeline.

**V2 - run**
- Features: cross-domain signals from ranked play (performance/frustration
  proxies) and social signals if available; multi-window trend features
  rather than single-window snapshots.
- Model class: revisit the PRD's out-of-scope uplift/causal framing - move
  toward an uplift-aware model that jointly optimizes who to target and with
  what offer, not just who is at risk.
- Timeline *(assumption)*: next 1-2 quarters.
- Headcount *(assumption)*: a dedicated small team (2-3 ML engineers/data
  scientists + 1 data engineer), reflecting this becoming a persistent
  retention system rather than a one-off model.

## Change log

- 2026-09-20: Initial Quick-POC draft written from `prd/riot-churn.md`.
