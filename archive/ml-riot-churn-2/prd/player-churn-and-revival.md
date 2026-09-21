# PRD: Player Churn and Revival

Practice project. Restarted from `ml-riot-churn-1` (where the deep-dive was
drafted before the PRD, out of order) to run the Definition checklist first,
properly, via `ml-system-design-prd`.

## Problem

Too many players are drifting away, and the studio has no per-player
early-warning signal today — only simple recency-based promotion rules, which
fire too late to act on: by the time recency alone flags a player, they're
already gone. There's also no signal at all for which already-inactive
players are worth trying to win back.

**Why now:** retention/LTV has been named an explicit organizational
priority, and content-cadence investment decisions want to be backed by a
defensible per-player engagement signal rather than aggregate DAU/MAU trends
or gut feel.

**Pain point today:** live-ops has no proactive targeting — recency is the
only lever, and it's reactive by construction.

## Requirements

### Scope

**Must-have:** two separate models, not one unified model, because the
populations and feature windows genuinely differ:
- **Lapse model** — risk score for players who are currently active
  (features from their trailing engagement window).
- **Revival model** — likelihood of return for players who are currently
  inactive (features from their lifetime history up to the point they
  lapsed).

**Out of scope for this project:**
- LTV / player value modeling (a separate, related but distinct project).
- The day-180 comeback-offer campaign's causal/uplift analysis (a separate
  next-best-action project — this project only needs to *exclude* those
  players from evaluation, not model the campaign itself).
- Any downstream notification/delivery/CRM integration. This project ends at
  a risk/return score; acting on that score is an explicit dependency
  outside this project's scope.

### Non-functional

Batch job — no latency or availability SLA, since there's no live serving
system in scope. At the current data scale (12,000 players, 748,811 activity
rows), this isn't even a "give it a few minutes" constraint: measured on this
machine, loading both CSVs takes ~0.22s, building trailing-28-day aggregate
features takes ~0.03s, and fitting a logistic regression on the resulting
~5,700-row feature table takes ~0.03s — well under a second of core compute.
The practical ceiling is exploratory/iteration time, not runtime.

## Metrics

### Offline

- **PR-AUC** (primary) — appropriate given the ~8% positive rate for both
  tasks; ROC-AUC would look inflated on this imbalance.
- **Precision, recall, F1** at a chosen operating threshold (secondary) —
  concrete enough for a stakeholder conversation about tradeoffs.
- **Precision-at-top-decile** — even though the actual intervention is out
  of scope, any realistic use of this score is budget-constrained ("reach
  out to the top N% flagged"), so ranking quality at the top matters more
  than overall calibration.

### Online

Not applicable. There is no live system in this project's scope to run an
A/B test against or guard with online metrics.

## Team

**Stakeholders:**
- **Live-ops / player-retention team** — primary consumer; would act on the
  risk and return scores if this were productionized.
- **Data-science leadership** — secondary stakeholder; wants a reusable
  player-state signal aligned with the org's retention/LTV priority, not a
  one-off model.

**Dependencies:** none blocking this project directly. A real
notification/offer-delivery system would be the actual actuator for these
scores, but per Scope, integrating with one is explicitly out of scope here.

### Reuse

No existing reusable feature-table or player-state pipeline was found
in this repo (checked directly against the codebase, not assumed) — this
project starts from a clean slate on the data-engineering side. No downstream
consumers exist to design against, since delivery integration is out of
scope.
