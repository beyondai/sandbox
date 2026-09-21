# High-level Design: Player Churn and Revival

Builds on `prd/player-churn-and-revival.md`. Two independent models, both
batch/offline per the PRD's scope (no downstream serving integration in
scope).

## ML framing

- **Lapse model**: binary classification — P(player has zero activity in the
  next 28 days | active in the trailing 7 days as of the scoring cutoff).
- **Revival model**: binary classification — P(player returns within the
  next 14 days | inactive as of the scoring cutoff). Note the asymmetric
  horizon versus the lapse model (28 days vs. 14) — a deliberate choice, not
  an inconsistency: an active player's near-term trajectory is meaningfully
  read over four weeks, but a return signal 14 days out is more actionable
  than one 28 days out, and revival is a rarer, sharper event than lapse.

## Architecture

Batch/offline only — no real-time inference path, per the PRD's explicit
scope (no downstream serving/notification integration in this project).

**Offline training pipeline:**

```
players.csv, activity.csv, content_calendar.csv
        │
        ▼
Cutoff-bounded feature build (day < c only)
  ├─ Lapse features:   trailing-28d activity/wins/party-share/minutes,
  │                     recency, tenure, region/platform/acquisition
  └─ Revival features: lifetime activity/wins/party-share/minutes,
                        recency, tenure-at-lapse, days-to-next-content-event
        │
        ▼
Label build (day >= c, strictly separate from feature window)
  ├─ Lapse label:   no activity in [c, c+28)
  └─ Revival label: any activity in [c, c+14)
        │
        ▼
Train/test split by cutoff (train c=135, test c=180,
  campaign-treated players excluded from c=180 population)
        │
        ▼
Two trained models (lapse, revival) + evaluation report
  (PR-AUC, precision/recall/F1, precision-at-top-decile)
```

**Offline/batch scoring pipeline** (how the trained models would be run on
a schedule, if this moved past the practice/evaluation stage):

```
Latest players.csv, activity.csv snapshot
        │
        ▼
Same feature build as training, cutoff = "today"
        │
        ▼
Trained lapse model ──► lapse risk score per active player
Trained revival model ──► revival likelihood per inactive player
        │
        ▼
Scores written to a batch output (table/file) — consumed by
live-ops/retention (per PRD's stakeholders); no live request/response
path exists in this project's scope.
```

## Phasing

Session-based, not calendar/headcount — this is a solo practice project
(headcount: 1, throughout).

- **V0 (baseline session)**: recency-only baseline for lapse (days since
  last active, thresholded/ranked); no model training. Establishes the
  floor. Already partially done via the independent monkey-mode track
  (`monkey-mode/`, run against the prior `ml-riot-churn-1` project) — its
  class-weighted logistic regression baseline hit PR-AUC 0.477 against a
  0.30 soft target, which is a useful ceiling-check reference even though
  that run predates this project's PRD/high-level design.
- **V1 (core-model session)**: from-scratch L2-regularized logistic
  regression (gradient descent) for both lapse and revival, each trained
  and evaluated on its own population per the PRD's metrics. Reference-
  checked against `sklearn.linear_model.LogisticRegression` for
  correctness, not for the number to report.
- **V2 (stretch session)**: discrete-time hazard reformulation of the
  lapse model (one row per player-active-period, handles censoring
  properly) — only if V1 is solid and time remains; not required to call
  this project done.
