# Round 4

Current best going in: F1 = 0.6667 (Logistic Regression, C=0.1, + ticket_rate). Candidates this round: 2 (default).

| Candidate | Hypothesis | F1 | vs. best |
|---|---|---|---|
| failure-rate | Extend round 3's rate-normalization pattern to payment_failures_last_90d | 0.6667 | Tied, not an improvement |
| svm | New model family: SVC (RBF kernel, balanced class weight) | 0.6415 | Worse |

**Outcome: discarded.** Neither cleared `best_metrics.json`'s F1 (0.6667) by `improvement_tolerance`. Current best unchanged.

Non-improvement streak: **1 / 5**.
