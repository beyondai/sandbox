# Round 1

Current best going in: F1 = 0.6296 (Logistic Regression, seeded from `modeling/03-train.md`).

| Candidate | Hypothesis | F1 | vs. best |
|---|---|---|---|
| random-forest | Swap model family to RandomForestClassifier (n_estimators=100, balanced) | 0.625 | Worse |
| payment-failure-flag | Add binary `had_payment_failure` feature (raw column was flagged highly skewed) | 0.6296 | Tied, not an improvement |

**Outcome: discarded.** Neither candidate cleared `best_metrics.json`'s F1 (0.6296) by the `improvement_tolerance` (0.5% relative) — the payment-failure-flag candidate tied exactly, consistent with Logistic Regression being linear (a binary transform of an already-included raw feature adds no new separable information). Current best is unchanged.

Non-improvement streak: **1 / 5** (`patience`).
