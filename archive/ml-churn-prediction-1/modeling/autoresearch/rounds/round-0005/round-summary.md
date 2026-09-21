# Round 5

*Test run: `patience` temporarily lowered to 3 (from 5) in `program.md` to bound a live test of "until plateau" mode — reverted after the test. See `SKILL-IMPROVEMENTS.md` / conversation for context.*

Current best going in: F1 = 0.6667 (Logistic Regression, C=0.1, + ticket_rate). Candidates this round: 2 (default).

| Candidate | Hypothesis | F1 | vs. best |
|---|---|---|---|
| usage-rate | Add `usage_per_tenure` = monthly_usage_hours / (tenure_months + 1), analogous to ticket_rate but for usage | 0.6792 | **Better (+0.0125, +1.87% relative)** |
| l1-penalty | Switch regularization type from L2 to L1 (sparsity/feature selection), same C=0.1 | 0.6316 | Worse |

**Outcome: promoted.** `usage-rate` beat `best_metrics.json`'s F1 (0.6667). Promoted to `experiment.py` / `best_metrics.json` and `modeling/04-evaluate.md`/`.json`. Same path-depth fix applied on promotion, re-verified. Note: overfit gap is now essentially zero (train 0.678 vs. test 0.679) — plausible sampling noise at this dataset size (~120 test rows), not a concern, but worth tracking if it continues.

Non-improvement streak: **0 / 3** (test `patience`) — reset, this round improved. Multi-round mode continues automatically to round 6.
