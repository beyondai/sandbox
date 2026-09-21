# Round 3

Current best going in: F1 = 0.6415 (Logistic Regression, C=0.1). Candidates this round: 2 (default).

| Candidate | Hypothesis | F1 | vs. best |
|---|---|---|---|
| stronger-regularization | Push further: C=0.01 and C=0.03 (both identical) | 0.6415 | Tied, not an improvement |
| ticket-rate | Add `ticket_rate` = support_tickets_last_90d / (tenure_months + 1), grounded in the original coefficient analysis | 0.6667 | **Better (+0.0252, +3.93% relative)** |

**Outcome: promoted.** `ticket-rate` beat `best_metrics.json`'s F1 (0.6415) well past the `improvement_tolerance` (0.5%). Promoted to `experiment.py` / `best_metrics.json` and `modeling/04-evaluate.md`/`.json`. Same path-depth fix as round 2 applied on promotion (`parents[5]` → `parents[2]`), re-verified independently before trusting it.

Non-improvement streak: **0 / 5** (reset — this round improved).

*Note: both candidate subagents this round independently caught and corrected a mistake in my own dispatch instructions (I told them to use `parents[2]` for their own, deeper candidate location — they correctly used `parents[5]` instead, matching the depth their files actually sit at). No bug reached the files; worth remembering that the fix only applies at promotion time, not at a candidate's own working location.*
