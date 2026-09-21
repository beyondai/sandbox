# Pointwise classification instead of learning-to-rank

We're framing the KKBOX repeat-listen prediction as pointwise binary
classification - one independent probability per (user, song) row -
rather than learning-to-rank. The competition's own eval metric
(AUC on independent per-row probabilities) matches pointwise
classification directly, but a "recommendation system" framing might
lead a future reader to expect a ranking loss (pairwise/listwise)
instead, since ranking is the more natural framing for
"recommend music." This decision forecloses that without saying so
elsewhere, so it's worth recording.

## Considered options

- **Learning-to-rank** (pairwise/listwise loss, e.g. LambdaMART):
  matches the "recommendation" framing more naturally and could
  exploit within-user relative ordering of candidates. Rejected
  because the competition's own metric (AUC on independent
  probabilities) doesn't reward ranking quality within a user's
  candidate set, and the labeled rows aren't naturally grouped into
  per-user candidate lists for training a ranker.
- **Pointwise binary classification** (chosen): matches the
  competition's metric and label structure exactly, is simpler to
  build and evaluate as a POC baseline, and leaves room to reframe as
  ranking later if this became a real production recommender.
