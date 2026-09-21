# Round 6

*Test run continued automatically from round 5 (streak was 0/3, well below patience — no pause, no human check-in, per the mode's documented behavior).*

Current best going in: F1 = 0.6792 (Logistic Regression, C=0.1, + ticket_rate + usage_per_tenure). Candidates this round: 2 (default).

| Candidate | Hypothesis | F1 | vs. best |
|---|---|---|---|
| drop-raw-features | Simplify: drop raw tenure/usage/tickets columns, keep only rate features + payment_failures | 0.5926 | Worse — lost signal, not redundancy |
| mlp | New model family: MLPClassifier(16,8), same features | 0.7442 | **Better (+0.065, +9.57% relative) — largest gain this session** |

**Outcome: promoted.** `mlp` cleared a real due-diligence check before promotion, not just the metric comparison: got a `ConvergenceWarning` (500 iterations, didn't fully converge) and the jump was unusually large for this session, so checked the train/test gap specifically before trusting it. Gap = 0.025 (train 0.769, test 0.744) — small, in line with or better than the linear models' gaps, not an overfitting red flag. Promoted to `experiment.py` / `best_metrics.json` / `04-evaluate.md`/`.json`. Same path-depth fix applied.

Non-improvement streak: **0 / 3** (test `patience`) — reset, this round improved. Multi-round mode continues to round 7.
