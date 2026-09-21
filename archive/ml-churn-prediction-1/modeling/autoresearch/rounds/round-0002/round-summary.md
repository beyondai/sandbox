# Round 2

Current best going in: F1 = 0.6296 (Logistic Regression, C=1.0, from round 1's unchanged seed). Candidates this round: 2 (default).

| Candidate | Hypothesis | F1 | vs. best |
|---|---|---|---|
| regularization | Tune Logistic Regression's C (tried 0.1 and 10.0) | 0.6415 | **Better (+0.0119, +1.89% relative)** |
| gradient-boosting | Swap to GradientBoostingClassifier (different ensemble style than round 1's Random Forest) | 0.6154 | Worse |

**Outcome: promoted.** `regularization` (C=0.1) beat `best_metrics.json`'s F1 (0.6296) by +1.89% relative, clearing the `improvement_tolerance` (0.5%). Promoted to `experiment.py` / `best_metrics.json`, and to `modeling/04-evaluate.md`/`.json` (the dashboard's Final Results tab now reflects this). Caught and fixed a real bug during promotion: the candidate's data path was computed relative to its own file depth (`parents[5]`), which was wrong once copied to `experiment.py`'s shallower location — corrected to `parents[2]` and independently re-verified (same F1) before trusting it.

Non-improvement streak: **0 / 5** (reset — this round improved).
