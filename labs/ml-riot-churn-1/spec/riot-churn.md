prd-hash: 0bf48388c3885ffff4745c258e59623047b288a9
high-level-hash: c3494a1db27f705ca20e4844bce58b753a3e8eb6

# Spec: Riot Churn

## Problem Statement

Players quietly drift away from the game with no system flagging it ahead of
time. The only existing response is a reactive day-180 comeback campaign.
Predicting risk earlier lets live-ops intervene before a player has already
gone quiet, protecting matchmaking pool health and shop/cosmetic revenue.

## Solution

Predict, for each currently active player, the probability they will lapse
or churn within the next 60 days. This folder builds one binary classifier
(active vs. lapsed/churned) - not the 3-class or uplift/causal variants,
which are later, separate efforts.

- Label: observed state at a 60-day forward horizon from the scoring date,
  collapsed to active (0) vs. lapsed/churned (1).
- Scoring population: players active in the trailing 30 days, scored weekly.
- Unit of prediction: one player, as of one scoring date, with trailing
  30/60/90-day feature aggregates.
- Exclusions: players in an onboarding grace period (first 14 days, covered
  by the separate `newplayer` dataset); players inside an active
  comeback-offer window during label construction, to avoid the campaign's
  own effect contaminating the churn label.
- Architecture: batch only, no real-time path. Weekly scoring job reads
  `players`, `activity`, `purchases` tables, builds trailing-window
  features, scores with the trained model, writes a `risk_score` table
  consumed by the existing comeback-campaign targeting mechanism.

## Implementation Decisions

- V0 model class: baseline - logistic regression or a single small tree
  ensemble (matches the monkey-mode baseline).
- V0 features: activity recency/frequency aggregates, basic monetization
  totals, static profile fields (region, platform, acquisition_source).
- V1 model class (future): tuned gradient-boosted trees with calibrated
  probabilities, richer trend/RFM features.
- V2 model class (future): uplift-aware targeting model, cross-domain
  (ranked/social) features.
- Source tables: `players.csv`, `activity.csv`, `purchases.csv` under
  `data/riot-synthetic/synthetic-data/data/lifecycle/`. `campaign.csv` and
  `content_calendar.csv` excluded from features (leakage / not per-player).
- No ADRs recorded yet for this project.

## Testing Decisions

- Primary offline metrics: F1 and ROC-AUC on a held-out split.
- Secondary offline metric: precision@k (top 10-20% highest-risk players),
  since live-ops can only act on a limited list.
- Guardrails (online, once deployed): reactivation-rate lift must not come
  with cost-per-reactivation regression or an increase in the false-positive
  discount rate.
- Split rule: not yet set - `ml-modeling-data` records the actual train/test
  split and cutoffs.

## Out of Scope

- Causal/uplift modeling of the comeback campaign's effect.
- Real-time/streaming inference.
- 3-class (active/lapsed/churned) distinction in v0.
- Automated triggering of interventions - this system informs, it does not
  act.
- Champion/match-level churn drivers from the `ranked` dataset.
