# Asymmetric horizons: 28-day lapse vs. 14-day revival

The lapse model predicts 28 days out; the revival model predicts 14 days
out. A reader familiar with the lapse model might expect the same horizon
for revival, so this is recorded rather than left implicit.

## Considered options

- **Symmetric 28-day horizon for both** (rejected): simpler to explain, but
  a return signal 28 days out is much less actionable than one at 14 days,
  and revival is a rarer, sharper event than lapse - a longer window mostly
  adds noise rather than signal.
- **14-day revival horizon** (chosen): tighter window matched to how
  quickly a revival intervention would need to act, at the cost of a
  smaller, more imbalanced positive class (2.6-3.7% vs. ~4-5% measured by
  an earlier 28-day draft of this project) - flagged in
  `design/deep-dive.md` as something to watch when judging revival PR-AUC.
