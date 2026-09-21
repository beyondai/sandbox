# PRD: Player churn at lifetime day 28 (60-day window)

- Project: `labs/ml-churn-1/`
- Mode: Quick POC
- Date: 2026-09-20
- Source: `notes/riot-practice-churn-3.md` (initial prompt + `#to-prd` answers), one grilling round
- Data: `data/riot-synthetic/synthetic-data/data/lifecycle/` (players, activity, purchases, campaign, content_calendar; `_truth/` is a grading key, never a modeling input)

## Problem

"Too many players are drifting away. Figure out who's staying and who is
leaving." Riot's lifecycle/retention team sees new-player D28 retention
sliding and wants a per-player churn-risk score at lifetime day 28 so the
CRM/lifecycle team can aim retention interventions (offers, content nudges)
at the players most likely to leave. Why now: a lapsed player costs far more
than a nudge, and targeting is currently blind.

## Label definition

Option (a) with the window widened by the user (2026-09-20 PRD update):
prediction point is lifetime day 28 (absolute day `signup_day + 28`).
Churned = 1 if the player has zero activity rows in lifetime days 28-87
inclusive (a **60-day** inactivity window after the prediction point), else
0. Features use only data with day < `signup_day + 28` plus static player
attributes. Only players whose full label window is observable are included
(`signup_day + 87 <= 269`; max signup_day is 179, so all 12,000 qualify).

Framing: this is still *early-lifecycle* churn, but a 60-day window means
"gone for two months", which is closer to a true lapse than the 28-day
version. The generator's own churn state is measured at absolute day 180 and
is not this label. Positive rate 0.30 (0.29 excluding the 326 never-engaged
players); the 28-day window used by the monkey-mode baseline gave 0.33.

## Requirements - scope

Must-haves for this version:

1. A labeled table built from `lifecycle/` logs per the label definition.
2. One batch-scored binary classifier giving a churn probability per player
   at lifetime day 28.
3. Offline evaluation against a recency-rule baseline
   (`days_since_last_activity` alone).
4. A ranked list / threshold the lifecycle team can act on.

Nothing served online.

## Requirements - out of scope

- Real-time / online scoring
- Uplift / treatment-effect modeling (the day-180 `campaign.csv` offer is a
  separate project)
- Choosing *which* intervention to send
- Revenue / LTV prediction
- The `ranked/`, `shop/`, `newplayer/` datasets
- `_truth/` as a feature (eval sanity checks only)
- Multi-class churned/lapsed/active - binary only
- Later-lifecycle churn (day-180 style)
- Automated retraining

## Requirements - non-functional

- Daily batch: score every player reaching lifetime day 28 that day
  (hundreds/day in this data; assume up to 100k/day in production).
- Latency: whole batch within 2 hours (user's number); no per-request
  latency target.
- Availability: best-effort; a missed day re-runs the next day.
- The POC runs end-to-end on a laptop in minutes.

## Metrics - offline

- Primary: PR-AUC (average precision) on held-out data, reported against the
  positive rate (0.30 with the 60-day window).
- Secondary: ROC-AUC; F1, precision and recall at the chosen threshold
  (user-added); precision/recall at the top 20% of scored players (assumed
  CRM contact budget).
- Key metric added by user (2026-09-20 PRD update), choice of metric is an
  assumption pending confirmation: **Brier score** (mean squared error of the
  predicted probability), reported against the constant positive-rate
  predictor. Reason: the output is a probability used with a threshold and a
  contact cap, so calibration matters as much as ranking; PR-AUC does not
  check it. Alternatives considered: lift@top-20% over the recency rule
  (mostly covered by precision@top-20% plus the baseline comparison) and
  per-cohort PR-AUC spread (a stability check, better placed in monitoring).
- Baseline to beat: the `days_since_last_activity` rule alone. The
  monkey-mode run shows it carries most of the signal (~0.31 of 0.76 PR-AUC
  from that feature), so beating it is the real test.
- Split: hold out the latest signup cohorts by `signup_day`, not a random
  split - `signup_day` was the #2 feature in the baseline and a random split
  overstates generalization to new cohorts.
- Reference point: monkey-mode baseline (HistGradientBoosting, random split,
  **28-day** window - not directly comparable to the 60-day label) PR-AUC
  0.76, ROC-AUC 0.90, F1 0.79 - see `monkey-mode/report.md`.

## Metrics - online

If shipped: A/B of model-targeted vs. random-targeted intervention on

- D56 retention rate
- Active days in the 28 days after contact

Guardrails (must not regress):

- Offer-driven revenue per player
- Contact volume stays within the CRM budget
- No region/platform systematically excluded from targeting

Stated, not measured, in the POC.

## Team

- Owner: the user (solo practice project).
- Stakeholders to inform: lifecycle/CRM team (consumer of scores); game
  analytics (owns the activity/purchase logs).
- Dependencies: a fresh daily `lifecycle/` extract. Nothing downstream blocks
  on this POC.

## Team - reuse

- Reuse: the repo's `ml-modeling-*` chain (dataset builder, experiment
  tracker, dashboard); `monkey-mode/baseline.py` as the starting point for
  feature aggregation.
- Downstream consumers: the CRM targeting list; later, an uplift model that
  could take this score as a feature.

## Change log

- 2026-09-20: user widened the churn window from 28 to 60 days and asked for one more key eval metric (Brier score added, pending confirmation).
