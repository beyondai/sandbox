# Autoresearch Round 2

Candidates this round: 2. Neither repeated a round-1 hypothesis
(early stopping / dropping `TotalCharges_residual`).

Design docs re-checked at round start: `prd/kaggle-churn.md` and
`design/high-level.md` hashes still matched `spec/kaggle-churn.md`'s
pinned hashes. No drift to note.

## Candidate 1 — larger trees (`max_leaf_nodes=63`)

Result: AUC-ROC **0.9158** vs. baseline 0.9155 — +0.033% relative.
**Discarded** — below the 0.5% improvement threshold, a tie within
noise.

## Candidate 2 — L2 regularization (`l2_regularization=1.0`)

Result: AUC-ROC **0.9157** vs. baseline 0.9155 — +0.022% relative.
**Discarded** — same reason.

## Outcome

No candidate improved. `best_metrics.json` unchanged (AUC-ROC 0.9155,
`hist_gradient_boosting`, `max_iter=100`). Non-improvement streak: **2**
(of `patience: 5`).

Session stopping here: the requested 3-minute wall-clock duration has
elapsed (2 rounds, 4 candidates total, ~170s of subagent work plus
scaffolding). Not a plateau stop (streak 2 < patience 5) — a duration
stop.
