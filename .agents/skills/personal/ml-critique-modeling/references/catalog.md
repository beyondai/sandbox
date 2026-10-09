# Modeling lens catalog

Contents: A. Problem and baseline | B. Training dataset and labels | C. Split
and validation | D. Leakage | E. Features | F. Model choice | G. Objective,
optimizer, and training | H. Tuning | I. Evaluation | J. Interpretability and
sanity | K. Reproducibility and handoff

Each item is one check. Each item has:
- **Check**: what to examine.
- **Mistakes**: the common failures.
- **Remedies**: the standard alternatives to propose.

`[C]` marks a classic-mistake item. Brief mode uses only `[C]` items and
the playbook's classic mistakes. Normal mode uses all items.

Sections: A Problem and baseline, B Training dataset and labels, C Split
and validation, D Leakage, E Features, F Model choice, G Objective,
optimizer, and training, H Tuning, I Evaluation, J Interpretability and
sanity, K Reproducibility and handoff.

---

## A. Problem and baseline

**A1 [C]. The task agrees with the PRD and the spec.**
- Mistakes: the report solves a different problem (different horizon,
  population, or target) from the spec.
- Remedies: restate the spec's framing at the top of the report. Fix the
  drift, or record it as an upstream change.

**A2 [C]. The baseline is correct and strong.**
- Mistakes: compare only with a random model or a majority class.
- Remedies: the playbook's baseline. At minimum: the prior rate, the
  current rule, and a simple model (logistic regression or default GBDT).
  Ranking: popularity and recency. Forecasting: seasonal naive.

**A3. The lift is measured against the strongest simple baseline.**
- Mistakes: lift over the weakest baseline in the table.
- Remedies: report the lift over the best simple baseline.

## B. Training dataset and labels

**B1 [C]. The training population is the same as the scoring population.**
- Mistakes: train on all users, score only active users. Train on
  approved cases, score all cases.
- Remedies: apply the scoring eligibility rule to the training rows.

**B2 [C]. The labels are correct.**
- Mistakes: the label window overlaps the feature window. Censored rows
  (horizon not complete) are labeled negative. Noisy labels with no check.
- Remedies: label in (T, T + H]. Remove rows whose horizon is not
  complete. Examine a sample of labels by hand.

**B3 [C]. Each row has an observation date, and features use only earlier
data (point-in-time correctness).**
- Mistakes: features from the latest snapshot of a table, joined to old
  labels.
- Remedies: a point-in-time join. Each feature is computed as of the row's
  observation date.

**B4. No duplicates, and no entity in both train and test.**
- Mistakes: the same user in many snapshot rows, split at random.
- Remedies: deduplicate. Group the split by entity, or split by time.

**B5. The class balance is reported.**
- Mistakes: no positive rate, so no reader can judge the metrics.
- Remedies: the positive rate in train, validation, and test.

**B6. Sampling is corrected in the calibration.**
- Mistakes: negatives down-sampled, then the scores used as probabilities.
- Remedies: correct with the sampling rate, or recalibrate on data that was
  not sampled.

**B6a [C]. Negatives are built correctly** (implicit labels only).
- Mistakes: random negatives only. The user's own positives or items not
  available at that time in the negative pool. Test negatives sampled the
  same easy way as train, so offline metrics are too high.
- Remedies: a mix of random and hard negatives (shown but not engaged),
  a stated ratio and pool, a correction (logQ or the sampling rate), and
  test candidates from the production distribution.

**B7. Data cleaning does not remove a population without a record.**
- Mistakes: drop rows with nulls, and remove all new users.
- Remedies: report the rows removed by each rule and the population that
  they belong to.

## C. Split and validation

**C1 [C]. The split is the same as production.**
- Mistakes: a random split on time-dependent data.
- Remedies: a time-based split with the production cadence, and a gap
  (embargo) equal to the label horizon.

**C2. The cross-validation agrees with the split.**
- Mistakes: random K-fold CV, then a time-based test.
- Remedies: time-series CV or grouped CV with the same rule as the test
  split.

**C3 [C]. The test set is used only one time.**
- Mistakes: model selection, early stopping, or threshold selection on the
  test set.
- Remedies: a separate validation set for all selection. One final test
  score.

## D. Leakage

**D1 [C]. No target leakage.**
- Mistakes: a feature that comes from the label, or from an event after
  the outcome (for example "cancellation_reason" in a churn model).
- Remedies: remove it. Compare each feature's timestamp with the label
  time.

**D2 [C]. No temporal leakage.**
- Mistakes: rolling aggregates with windows that cross the cutoff. Global
  statistics computed on all dates.
- Remedies: compute all aggregates with data before the observation date.

**D3 [C]. No encoding leakage.**
- Mistakes: target, mean, or leave-one-out encodings fit on all the data.
- Remedies: fit encodings inside each training fold (out-of-fold
  encoding).

**D4. No preprocessing leakage.**
- Mistakes: a scaler, imputer, or feature selection fit before the split.
- Remedies: a pipeline that fits each step on the training fold only.

**D5 [C]. Warning signs are examined.**
- Mistakes: one feature with most of the importance. AUC > 0.95 on a
  difficult problem. A test score better than the validation score.
- Remedies: the leakage probe (see the SKILL.md "Evidence" section). Explain
  the result before you accept it.

## E. Features

**E1. The feature set agrees with the problem type.**
- Mistakes: generic raw columns only.
- Remedies: the playbook's typical features.

**E2 [C]. The standard strong features are present.**
- Mistakes: no recency or trend features for a behavior problem. No
  user-item affinity for a recommender.
- Remedies: recency, frequency, monetary value, trends (short window
  against long window), ratios. Domain features from the playbook.

**E3 [C]. Each feature is available at serving time with the same logic.**
- Mistakes: a feature that needs data with a 2-day delay, in a model that
  scores at once.
- Remedies: mark each feature online or offline, and give its delay.
  Simulate the delay in training.

**E4. High-cardinality categoricals are encoded correctly.**
- Mistakes: one-hot encoding on 100k IDs. Label encoding used as a number
  in a linear model.
- Remedies: out-of-fold target encoding, hashing, embeddings, or native
  categorical support (LightGBM, CatBoost).

**E5. Missing values that have meaning are kept as a feature.**
- Mistakes: fill with the mean, and lose the signal "never used this
  feature".
- Remedies: a missing-indicator feature, or native missing handling in
  GBDT.

**E6. Feature selection is justified and stable.**
- Mistakes: select by importance on one run, on the test set.
- Remedies: select on validation folds. Examine stability across folds.

## F. Model choice

**F1 [C]. The model family agrees with the data.**
- Mistakes: a deep network on a small tabular dataset. A linear model on
  strong interactions.
- Remedies: GBDT is the strong default for tabular data. Neural networks
  for large data or unstructured input. Sequence models for ordered
  events. Embeddings for high-cardinality IDs.

**F2. The complexity agrees with the data size, latency, and
interpretability needs.**
- Mistakes: a 500-tree ensemble where a 20 ms budget or a reason code is
  necessary.
- Remedies: a smaller model, distillation, or a monotonic GBDT.

**F2a. The architecture is justified.**
- Mistakes: attention or a deep MLP with no sequence and no evidence that
  it beats a shallow model. An MLP left to learn crosses that a cross
  network models cheaply. Embedding sizes with no rule.
- Remedies: shallow before deep; DCN-v2 or DeepFM for explicit crosses;
  attention for sequences; an MLP head of 2-3 layers (for example 256 ->
  128 -> 64); embedding dims tied to cardinality. An ablation for each
  added block.

**F3 [C]. A fair comparison justifies the choice.**
- Mistakes: the winner got more tuning, more features, or a different
  split.
- Remedies: the same features, the same split, and the same tuning budget
  for each candidate.

**F4 [C]. The selected model passes the complexity gate.**
- Mistakes: a complex model is selected for a gain inside the noise, or
  for a gain smaller than its added running, maintenance, and
  explainability cost.
- Remedies: the gate: the gain is larger than the noise; its value is
  larger than the added cost; the comparison is with a fairly tuned
  simpler option. Show a cost table: the value of the gain, running cost,
  maintenance cost, explainability, and risk (rough values; `unknown` is
  valid).
  Select the simplest model inside the noise of the best. Show each added
  component with an ablation.

## G. Objective, optimizer, and training

**G1 [C]. The loss agrees with the metric and the decision.**
- Mistakes: MSE on a heavy-tailed target. Pointwise loss for ranking.
  Focal loss when calibrated probabilities are necessary.
- Remedies: log loss when calibration is important. A ranking loss
  (LambdaRank) for ranking. Quantile, Tweedie, or ZILN loss for skewed
  regression. A custom cost when the error costs are different.

**G2. The optimizer is correct.**
- Mistakes: default solver that does not converge. A fixed learning rate
  for a neural network. Too few boosting rounds with a high learning rate.
- Remedies: a solver that converges (examine the warnings). AdamW with a
  warm-up and decay schedule. Boosting with a low learning rate and
  early-stopped rounds.

**G3 [C]. Early stopping uses the validation set.**
- Mistakes: early stopping on the test set. The test score is then too
  high.
- Remedies: early stopping on validation only. Report the stopping round.

**G4. The regularization is correct.**
- Mistakes: no regularization, and a large train-to-test gap.
- Remedies: tune depth, minimum leaf size, L1 and L2, dropout, or weight
  decay on validation.

**G5. The class-imbalance method agrees with the metric.**
- Mistakes: oversampling (SMOTE) and then calibrated probabilities used.
  Class weights that move the threshold, then 0.5 used.
- Remedies: class weights or no change, then a threshold from the
  capacity. Recalibrate after resampling.

**G5a. The training setup and hyperparameters are recorded.**
- Mistakes: no record of the optimizer, learning rate, batch size,
  epochs, dropout, or hardware. A random forest with defaults and no
  stated depth or tree count. No training time.
- Remedies: record them. Typical starts: AdamW at 1e-3 (MLP) or 2e-5 to
  5e-5 (transformer fine-tuning) with warm-up and decay; batch 512-4096
  for tabular data; early stopping with patience 2-5; dropout 0.1-0.3.
  Random forest: 200-500 trees, full depth or 10-30, min leaf 1-5,
  `max_features="sqrt"`. GBDT: learning rate 0.05-0.1 with early-stopped
  rounds, 31-127 leaves, min child 20-100, subsampling 0.7-0.9. CPU for
  trees and small MLPs, GPU for large embeddings and attention.

**G6. Random seeds are set, and the results are deterministic.**
- Mistakes: one run, no seed. The result changes on the next run.
- Remedies: fixed seeds. Report the variance across 3 to 5 seeds.

## H. Tuning

**H1. The search space is correct.**
- Mistakes: a grid on unimportant parameters. A learning rate on a linear
  scale.
- Remedies: search the important parameters, on a log scale where
  applicable. Random or Bayesian search (Optuna), 30-100 trials for GBDT,
  20-50 for a DNN.

**H2. Each candidate gets the same tuning budget.**
- Mistakes: 200 trials for the favorite, defaults for the others.
- Remedies: the same number of trials or the same compute for each
  candidate.

**H3 [C]. The search uses the validation set, not the test set.**
- Mistakes: the best parameters selected by test score.
- Remedies: select on validation or CV. Score the test once.

**H4. A selected value at the edge of the search space is examined.**
- Mistakes: the best depth is the maximum value in the grid.
- Remedies: make the search space larger in that direction.

## I. Evaluation

**I1 [C]. The metric agrees with the class imbalance and the business
cost.**
- Mistakes: accuracy on 3% positives. ROC-AUC only, when the decision is
  the top k.
- Remedies: PR-AUC, recall@k, precision@k. nDCG or MAP for ranking. MASE
  or WAPE for forecasting.

**I2 [C]. The report uses the PRD primary metric and the guardrails.**
- Mistakes: the report gives a different metric from the PRD.
- Remedies: report the PRD metrics first, then the others.

**I3 [C]. The threshold comes from the capacity or the cost.**
- Mistakes: the default 0.5 threshold.
- Remedies: a threshold from the action capacity (top k%) or from the cost
  matrix. Report the metrics at that threshold.

**I4. Calibration is examined.**
- Mistakes: scores used as probabilities with no check.
- Remedies: a reliability table and the Brier score. Isotonic or Platt
  calibration on validation.

**I5 [C]. Uncertainty is given.**
- Mistakes: one number, no interval.
- Remedies: a bootstrap confidence interval, or the variance across seeds
  or folds.

**I6 [C]. The lift is larger than the noise.**
- Mistakes: a 0.002 AUC gain is called a win.
- Remedies: a paired bootstrap or a significance test
  (`../../ml-modeling/scripts/hypothesis_tester.py`).

**I7. Segment slices are reported.**
- Mistakes: only the global metric. A failure on new users is hidden.
- Remedies: metrics for each segment: new and old users, regions,
  platforms, cohorts, sensitive groups.

**I8. The overfit gap and the learning curves are examined.**
- Mistakes: no train score. No idea if more data can help.
- Remedies: report the train, validation, and test scores. A learning
  curve on training-set size.

**I9. Error analysis is done.**
- Mistakes: no look at the worst errors.
- Remedies: examine the top false positives and false negatives. Find the
  pattern, and turn it into a feature or a data fix.

**I10 [C]. The offline result can transfer to production.**
- Mistakes: evaluate on a population or period that the model will not
  serve.
- Remedies: a test set that is the same as the first production period
  and population.

## J. Interpretability and sanity

**J1. Feature importances and SHAP values agree with domain knowledge.**
- Mistakes: an ID or a timestamp is the top feature, and nobody asks why.
- Remedies: examine each top feature. Explain it, or remove it as a leak.

**J2. Partial-dependence directions are possible.**
- Mistakes: more activity predicts more churn, with no explanation.
- Remedies: examine the direction for the top features. Use monotonic
  constraints where the direction is known.

## K. Reproducibility and handoff

**K1 [C]. A person can make the same results again.**
- Mistakes: results from a notebook with a changed state. No data version.
- Remedies: a script or a clean notebook run, a fixed data snapshot, and a
  saved config.

**K2. Experiments are recorded, and artifacts have versions.**
- Mistakes: the winning model's parameters are not saved.
- Remedies: an experiment log
  (`../../ml-modeling/scripts/experiment_tracker.py`) and versioned model
  files.

**K3. The inference path uses the same code as the training path.**
- Mistakes: features re-written for serving. A skew that nobody tests.
- Remedies: one feature pipeline for both paths. A parity test on a sample
  of rows.

**K4. Serving latency and capacity are measured on the real artifact.**
- Mistakes: a latency claim with no measurement, or a mean in place of
  p99. A benchmark that times a batch and calls it a request. Capacity
  from the average load. No comparison with the PRD p99 target.
- Remedies: time the real scoring function (`serve.py`) after a warm-up:
  single-request p50/p99 and batch throughput (`bench_serve.py` in
  `ml-modeling-serve`). Replicas from the peak QPS with headroom, or the
  batch job time against its window. A plain verdict against the target.
