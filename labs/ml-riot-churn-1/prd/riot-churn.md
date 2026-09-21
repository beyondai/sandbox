# Riot Churn - Definition (PRD)

Mode: Quick POC. Confirmed by user as a single one-pass draft round, no
overrides.

## Problem

A live-service game has a growing player-drift problem: players quietly stop
coming back, and there is no system that flags this before it happens. The
lifecycle data already includes a day-180 "comeback" campaign
(`campaign.csv`), which shows the team already reacts to lapses after the
fact, but nothing predicts risk ahead of time.

Core problem: predict, ahead of the point a player has already gone quiet,
which players are on track to lapse or churn, so retention/live-ops can
intervene earlier and more precisely than the current reactive comeback
campaign.

Why now / link to goals: retention feeds everything downstream - ranked
matchmaking pool health, cosmetic/shop revenue (the `shop`/`purchases` data),
and the ROI of the existing comeback campaign, which today likely targets
reactively or broadly rather than by predicted risk. A working risk model
should make that existing campaign spend more efficient by targeting it.

## Requirements - scope

**Must-have (v0)**: a model that scores each active player's probability of
lapsing/churning within a lookahead window (e.g. next 30-60 days), built from
behavioral (`activity.csv`), monetization (`purchases.csv`), and profile
(`players.csv`) signals, refreshed on a batch cadence (daily or weekly).
Output is a per-player risk score, not an action.

**Out-of-scope for v0**:
- Causal/uplift modeling of the comeback campaign's effect (no use of
  `potential_outcomes.csv`).
- Real-time/streaming inference.
- 3-class (active/lapsed/churned) distinction - v0 is binary stay-vs-leave.
- Automated triggering of interventions - this system informs live-ops, it
  does not act on its own.
- Champion/match-level churn drivers from the `ranked` dataset.

## Requirements - non-functional

Dataset scale: ~12,000 players, ~750k activity rows, ~6,900 purchase rows -
small/mid enough that this is a batch pipeline, not a low-latency service.

Latency: scoring runs daily or weekly (hours of slack, not seconds); no p99
latency target needed since nothing serves this synchronously to a user.

Availability: best-effort batch job, no 24/7 SLA - a missed run just delays
that cycle's campaign list, it does not break player-facing functionality.

## Metrics - offline

F1 and ROC-AUC on a held-out split (consistent with the monkey-mode baseline),
plus precision@k (e.g. top 10-20% highest-risk players), since live-ops can
only act on a limited list and cares most about ranking quality at the top,
not overall accuracy.

## Metrics - online

Primary: reactivation-rate lift among players targeted by the comeback
campaign using model-driven risk scores, versus today's targeting
(random/broad or rules-based).

Guardrails:
- Cost per reactivated player must not regress (don't just spend more to get
  more reactivations).
- False-positive discount rate - the share of offer spend going to players
  who would have stayed anyway - must not increase versus the current
  baseline.

## Team

Stakeholders to inform: player retention / live-ops (owns campaign targeting
decisions), game economy/monetization (cares about shop revenue impact).

Collaborating team: CRM/growth, who operate the send mechanism behind
`campaign.csv`.

Blocking dependencies: none for v0 - it reads data that is already collected.

Blocked-on-this: any future campaign-automation work that wants to target by
predicted risk instead of fixed rules.

## Team - reuse

Reusable: the lifecycle data pipeline already exists (players/activity/
purchases are already being collected), and the comeback-offer send
mechanism already exists (`campaign.csv`) - v0 just needs to feed a risk
score into that existing targeting step rather than building new delivery
infrastructure.

Downstream consumers: the live-ops campaign targeting logic, and potentially
a risk-dashboard view for player-success/CRM.

## Change log

- 2026-09-20: Initial PRD written from a single Quick-POC grilling round (all
  seven Definition bullets), confirmed by the user with no overrides.
