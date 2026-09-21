# Autoresearch Round 1

Candidates this round: 2 (`program.md`'s `candidates_per_round`).

Design docs re-checked at round start: `prd/kaggle-churn.md` and
`design/high-level.md` hashes still matched `spec/kaggle-churn.md`'s
pinned hashes. No drift to note.

## Candidate 1 — more capacity + early stopping

Hypothesis: `max_iter=300, early_stopping=True, validation_fraction=0.1,
n_iter_no_change=10` instead of the fixed `max_iter=100`.

Result: **AUC-ROC 0.9155** — identical to baseline, 0.0% relative
change. **Discarded.** Early stopping converged to roughly the same
effective iteration count the fixed `max_iter=100` baseline already
reached — more capacity wasn't the bottleneck.

## Candidate 2 — drop `TotalCharges_residual`

Hypothesis: remove the engineered `TotalCharges_residual` column, which
`02-features.md` had already flagged as a low-confidence addition
(mutual_info 0.0096, weaker than any raw feature).

Result: **AUC-ROC 0.9153** — -0.02% relative change vs. baseline.
**Discarded** (below the 0.5% improvement threshold either direction).
Confirms `02-features.md`'s read: the feature is neither hurting nor
meaningfully helping — cheap and harmless, not a real contributor
either.

## Outcome

**No candidate improved.** `best_metrics.json` unchanged (AUC-ROC
0.9155, `hist_gradient_boosting`). Non-improvement streak: **1** (of
`patience: 5`).
