# System lens catalog

Contents: A. Business goal and problem | B. Success metrics | C. Requirements
and scope | D. ML framing and labels | E. Data | F. Architecture | G. Modeling
plan | H. Phasing | I. Delivery, experiments, and operations | J. Post-delivery
and responsible ML | K. Cross-section consistency

Each item is one check. Each item has:
- **Check**: what to examine.
- **Mistakes**: the common failures.
- **Remedies**: the standard alternatives to propose.

`[C]` marks a classic-mistake item: the most likely P1 or P2. Check
order (most important first): the playbook's classic mistakes, then the
sections in order. Inside a section, check the `[C]` items first, then the
others in ID order. Each run uses all items. Coverage of the design and
modeling skills: `../../ml-critique/references/coverage.md`.

Sections: A Business goal, B Success metrics, C Requirements and scope,
D Framing and labels, E Data, F Architecture, G Modeling plan, H Phasing,
I Delivery and operations, J Post-delivery and responsible ML,
K Cross-section consistency.

---

## A. Business goal and problem

**A1 [C]. The business goal is clear and measurable.**
- Mistakes: "improve engagement" with no number. A goal that is a model
  metric, not a business result.
- Remedies: a business metric with a target and a date, for example
  "increase 30-day retention from 40% to 42% by Q3".

**A2. The goal connects to a team or company goal.**
- Mistakes: no reason why the company cares.
- Remedies: one line that links the metric to a company objective.

**A3. The document gives the reason for the work now.**
- Mistakes: no trigger, so the priority is not clear.
- Remedies: name the trigger: a new data source, a cost increase, a
  competitor, a scale limit.

**A4 [C]. ML is necessary.**
- Mistakes: ML for a problem that a rule or a report solves. No comparison
  with a heuristic.
- Remedies: estimate the heuristic's result first. Use ML only if the gap
  is worth the cost to build and maintain the model.

**A5 [C]. The document names the decision that the model controls.**
- Mistakes: a score with no user. No owner of the action.
- Remedies: name who uses the prediction, how, when, and the capacity of
  the action.

**A6. The cost of each error type is given.**
- Mistakes: false positives and false negatives treated as equal.
- Remedies: a cost estimate for each error type. Use it to select the
  metric and the threshold.

**A7. The value if the model works is estimated.**
- Mistakes: no size of the opportunity.
- Remedies: a rough estimate: population times the effect times the value
  for each unit.

## B. Success metrics

**B1 [C]. There is one clear primary metric.**
- Mistakes: 5 metrics with equal weight. No rule for a conflict.
- Remedies: one primary metric. The others are secondary or guardrails.

**B2 [C]. The offline metric is a good proxy for the online metric.**
- Mistakes: AUC offline, revenue online, and no argument that they move
  together.
- Remedies: an offline metric that matches the decision (for example
  precision at the capacity). Evidence from past launches that offline
  gains gave online gains.

**B3. Each guardrail metric has a name, a measurement, and a threshold.**
- Mistakes: "we will watch the user experience".
- Remedies: named guardrails with a maximum allowed change, for example
  "latency p99 +10 ms maximum, unsubscribe rate +0.1 pp maximum".

**B4. There is a realistic launch target.**
- Mistakes: no bar, or a bar with no baseline.
- Remedies: a target relative to the baseline, for example "+5% recall at
  the top 5% over the recency rule".

**B5 [C]. The metric agrees with the capacity of the action.**
- Mistakes: global AUC when the team can act on only k users.
- Remedies: precision@k, recall@k, or lift at the capacity.

**B6. Counter-metrics cover side effects.**
- Mistakes: optimize clicks, get clickbait. Optimize short-term revenue,
  lose retention.
- Remedies: a long-term metric or holdout as a counter-metric.

**B7 [C]. The ways the model can game the metric are named, each with a
check.**
- Mistakes: no intended behavior next to the primary metric. The model
  can score well with degenerate outputs (the same popular items for all
  users, repeat loops, near-duplicates, avoidance of hard cases), and no
  check would see it.
- Remedies: write the intended behavior in user terms. List the ways to
  game the metric, each with a guardrail or an output check. A person
  reads a sample of outputs for typical and edge-case inputs before
  launch. If the goal is a target level, not a maximum, optimize to the
  target. See `../../ml-design-principles.md`, Principle 2.

## C. Requirements and scope

**C1 [C]. The out-of-scope list is real and specific.**
- Mistakes: no list, or a list of things nobody planned to do.
- Remedies: list the tempting adjacent features that this version does not
  do.

**C2 [C]. A back-of-envelope estimate of the requirements and the cost
is made at the start.**
- Mistakes: no numbers, so the architecture cannot be judged. The
  estimate is skipped because the design "looks cheap" (a precompute, a
  small model). Nobody knows it is cheap until the estimate is done.
- Remedies: a quick estimate before the design: peak QPS (users x actions
  in the peak window), p99 latency, availability, data freshness, data
  size, and the order of magnitude of the training and serving cost. Mark
  each assumption. A full analysis needs the full design, so do not ask
  for it here: the deep dive refines the estimate (F4a, C5). Keep this a
  P1 also when the result looks trivial.

**C3. The numbers agree with the model class and the serving mode.**
- Mistakes: a large deep model in a 20 ms budget. A 1-hour freshness need
  with a daily batch.
- Remedies: a latency budget for each component, distillation, caching, or
  precompute.

**C4 [C]. The decision cadence justifies batch or real-time serving.**
- Mistakes: real-time serving for a weekly email. Batch for a fraud check
  at checkout.
- Remedies: batch when the decision is scheduled. Real-time only when the
  input changes inside the request.

**C5. The cost and the infrastructure budget are included.**
- Mistakes: GPU serving with no cost estimate.
- Remedies: cost for each 1k predictions, training cost, and a comparison
  with the value from A7.

**C5a [C]. The explainability need and the cost sensitivity are stated.**
- Mistakes: no statement, so no reader can judge if a complex model is
  acceptable.
- Remedies: state the explainability need (hard or soft) and the cost
  sensitivity (a budget, or `low`/`medium`/`high`, or `unknown`). A rough
  level is enough.

**C6. Privacy, compliance, and fairness constraints are identified.**
- Mistakes: PII in features with no review. Protected attributes with no
  plan.
- Remedies: a data review, retention rules, and the fairness slices to
  monitor.

**C7. Stakeholders, dependencies, and reuse are named.**
- Mistakes: no owner for the action. A blocking team (data, platform,
  legal) found late. A new component built when one exists.
- Remedies: the stakeholders to inform, the collaborating teams, the
  blocking and blocked dependencies, the existing components to reuse,
  and the downstream consumers of the output.

## D. ML framing and labels

**D1 [C]. The ML task type is correct.**
- Mistakes: classification when the decision is a ranking. Propensity when
  the decision is an intervention.
- Remedies: match the task to the decision: classification, ranking,
  regression, uplift, forecasting, or retrieval.

**D2 [C]. The label is a good proxy for the goal.**
- Mistakes: a convenient label (click) for a deep goal (satisfaction).
- Remedies: a deeper label (dwell, purchase, return), or a multi-task
  objective.

**D3 [C]. The label method is correct.**
- Mistakes: implicit labels used as truth. Annotation with no agreement
  measure. Label noise and label delay ignored.
- Remedies: an annotation guide with inter-rater agreement, a label
  maturity window, noise-robust training.

**D4 [C]. The label horizon agrees with the decision cadence and the time
to act.**
- Mistakes: a 7-day horizon when the action needs 10 days to work.
- Remedies: horizon = the action lead time plus the effect window.

**D5 [C]. The prediction time and the label window are precise, and do not
overlap.**
- Mistakes: "users who churn" with no snapshot date.
- Remedies: an explicit snapshot date T. Features before T. The label in
  (T, T + H].

**D6. The scoring population is correct.**
- Mistakes: score users who are already lost, or who are not eligible for
  the action.
- Remedies: an eligibility rule that is the same in training and serving.

**D7. Contaminated rows are removed.**
- Mistakes: users from a past campaign, test accounts, bots.
- Remedies: an exclusion list, or a treatment flag as a feature.

**D8. The unit of prediction is correct.**
- Mistakes: a row for each event when the decision is for each user.
- Remedies: one row for each decision unit, at decision time.

**D9 [C]. For an intervention, the framing predicts who responds.**
- Mistakes: target users at high risk who leave in all cases, or who stay
  in all cases.
- Remedies: uplift modeling on randomized data. At minimum, a holdout to
  measure the incremental effect.

**D10. Feedback loops are handled.**
- Mistakes: the model changes the data that it later learns from.
- Remedies: exploration traffic, logged propensities, a permanent holdout.

## E. Data

**E1 [C]. Each data source is named, with owner, volume, history, and
freshness.**
- Mistakes: "user data", "logs".
- Remedies: table names, owners, row counts, history length, update
  delay.

**E2 [C]. Each feature is available at serving time with the same
definition.**
- Mistakes: features from a warehouse table that updates daily, used in a
  real-time path. Training-serving skew.
- Remedies: mark each feature online or offline. Compute it with one
  definition for both paths.

**E3. The online and offline paths share feature definitions.**
- Mistakes: SQL for training, Java for serving. The 2 drift apart.
- Remedies: a feature store, or one shared feature library. Log served
  features and train on the logs.

**E4. Data quality, missing values, and backfill are examined.**
- Mistakes: a source with gaps or schema changes, not mentioned.
- Remedies: quality checks, a backfill plan for new features.

**E5 [C]. The training population is the same as the serving population.**
- Mistakes: train on approved users, serve on all applicants. Selective
  labels.
- Remedies: a random sample with labels, reject inference, or a
  population-matched training set.

**E6. There is a cold-start plan.**
- Mistakes: new users and new items get no score, or a bad score.
- Remedies: content features, segment priors, a heuristic fallback,
  exploration.

## F. Architecture

**F1 [C]. There are 2 diagrams: online inference and offline training.**
- Mistakes: one diagram that mixes the 2 paths.
- Remedies: 2 separate diagrams. The offline diagram names its source
  tables.

**F2 [C]. The architecture fits the problem type.**
- Mistakes: one stage over a large catalog. A model with no rules layer
  for fraud.
- Remedies: the playbook's standard architecture.

**F3. Caching and precompute are decided.**
- Mistakes: compute at request time what does not change in the request.
- Remedies: precompute embeddings and slow features. Cache the scores
  with a TTL.

**F4. The latency budget is divided among the components.**
- Mistakes: one total budget, no split.
- Remedies: a budget for each component: feature fetch, retrieval,
  ranking, rules.

**F4a. The capacity covers the peak load.**
- Mistakes: no capacity plan. Sizing for the average QPS. No headroom
  for spikes or a lost replica. A batch job with no check against its
  scoring window.
- Remedies: replicas = peak QPS x (1 - cache hit rate) / QPS per replica
  x headroom (1.3-1.5); autoscaling between average and peak; a
  degradation order under overload; a load test at the peak before
  launch. For batch: job time = population / throughput, well inside
  the window.

**F5. There is a retraining schedule, trigger, and promotion procedure.**
- Mistakes: "we will retrain periodically".
- Remedies: a schedule, a drift trigger, and an automated gate (the new
  model must pass the offline metric and the guardrails).

**F6. There is model versioning and lineage.**
- Mistakes: no way to know which model and data made a prediction.
- Remedies: a model registry, a model version in each prediction log.

**F7. Retraining fits the cadence of scheduled changes.**
- Mistakes: only a drift trigger. The scheduled upstream changes
  (product releases, catalog or rule updates, pricing or policy changes)
  are not listed. One retrain takes longer, or costs more, than one
  change cycle. Only the authors of the model can run it.
- Remedies: list the scheduled changes and their cadence. Give the
  retrain time and cost for each cycle, and show that it fits. Make each
  scheduled change a retrain or re-check trigger. Name the post-launch
  owner, who runs it from the runbook (I9).

## G. Modeling plan

**G0. The baseline has all its parts.**
- Mistakes: no status quo (what users do today). No floor, so no reader
  knows if the metric means anything. No decision when to build the
  baseline.
- Remedies: the status quo, the recommended baseline from the playbook,
  the floor (random, majority class, global popularity), and the build
  decision (now, later, or never).

**G1 [C]. The baseline is strong.**
- Mistakes: compare with random, or with a weak model.
- Remedies: the playbook's baseline. The current production rule if it
  exists.

**G1a. The feature list is concrete.**
- Mistakes: "user features, item features". No transform for a
  high-cardinality ID or for text. No source for each feature.
- Remedies: a list by group (user, item, context, cross), each with its
  source and its nontrivial transform (for example embeddings for
  `user_id`, TF-IDF or a text encoder for text). The playbook's typical
  features.

**G2. The model choice is justified.**
- Mistakes: a deep model on 50k tabular rows. A choice by fashion.
- Remedies: justify with data size, data type, latency, and
  interpretability. GBDT is the default for tabular data. Name the
  architecture and why: shallow before deep; a cross network (DCN-v2,
  DeepFM) for explicit feature crosses; a two-tower model for retrieval;
  attention only for sequences or history-candidate relations.

**G2a [C]. Each complex choice passes the complexity gate.**
- Mistakes: a deep model, a real-time pipeline, or a new data dependency
  with no comparison of its gain and its total cost.
- Remedies: the gate: the gain is larger than the noise; its value is
  larger than the added cost; the comparison is with a fairly tuned
  simpler option. Show a cost table: the value of the gain, running cost,
  maintenance cost, explainability, and risk (rough values; `unknown` is
  valid).
  If the gate fails, use the simpler option and keep the complex one as a
  later phase with a stated trigger.

**G3. The comparison of alternatives is fair.**
- Mistakes: the chosen model has all the tuning. The others are strawmen.
- Remedies: the same features, the same split, and the same tuning budget.

**G4 [C]. The loss agrees with the metric.**
- Mistakes: pointwise loss for a ranking metric. Uncalibrated scores used
  as probabilities.
- Remedies: a ranking loss for ranking. Log loss with calibration where
  thresholds or auctions use the score.

**G5. There is a plan for class imbalance and negative sampling.**
- Mistakes: no plan for 1% positives. Implicit labels (clicks only) with
  no stated negatives. Random negatives only. Unlabeled items treated as
  sure negatives. Evaluation on the training negatives.
- Remedies: class weights or threshold tuning. A negative plan: types
  (random, popularity-weighted, in-batch, hard: shown but not engaged),
  a ratio (often 4-10 per positive), the pool, and a correction (logQ, or
  the down-sampling rate). Evaluate on the production distribution.

**G5a. The training setup is stated.**
- Mistakes: "we will train a DNN" with no optimizer, learning rate,
  epochs, or hardware. A random forest with no depth or tree count. No
  training-time or compute estimate, so no running cost.
- Remedies: for a neural network: framework, optimizer (AdamW), learning
  rate and schedule (for example 1e-3 with warm-up and cosine decay),
  batch size, epochs with early stopping on validation, dropout (0.1-0.3)
  and weight decay. For trees: trees, depth or leaves, min leaf size,
  learning rate and rounds with early stopping. The hardware (CPU or
  GPU), the expected training time, and the tuning budget.

**G6 [C]. The evaluation plan mirrors production.**
- Mistakes: a random split for a time-dependent problem.
- Remedies: a time-based split or a rolling backtest with the production
  cadence.

## H. Phasing

**H1 [C]. V0 is simple and can ship.**
- Mistakes: V0 is the full deep model.
- Remedies: V0 is a heuristic or a simple model, with the full pipeline
  around it. Each later phase names the gain that justifies its added
  complexity.

**H2. Each phase gives measurable value.**
- Mistakes: a phase that is only infrastructure, with no metric.
- Remedies: each phase has a metric target and a decision gate. The
  gate checks more than the metric: the stability across seeds or
  retrains, the coverage of segments and edge cases, and the running
  cost.

**H3. The stretch work is separate.**
- Mistakes: research mixed into the commitments. A committed launch
  date depends on a method that the team has not yet shown to work on
  this problem.
- Remedies: put the research in a stretch phase. Keep the last proven
  version (the baseline or the previous phase) shippable, and keep
  improving it while the new method is tested. Name the date and the
  evidence that decide which version ships.

**H4. The timeline and the headcount are realistic.**
- Mistakes: 3 stages and a feature store in 4 weeks with 1 person.
- Remedies: compare with similar past projects. Cut the scope, not the
  quality.

## I. Delivery, experiments, and operations

**I1 [C]. The randomization unit is the same as the analysis unit.**
- Mistakes: randomize by session, analyze by user.
- Remedies: randomize at the analysis unit, or use the delta method or
  cluster-robust errors.

**I2 [C]. The A/B test has sufficient power.**
- Mistakes: no MDE, no duration, a stop when the result looks good.
- Remedies: a power calculation, a fixed duration (whole weeks), CUPED for
  variance reduction, no peeking (or a sequential test).

**I3. Network effects and interference are examined.**
- Mistakes: user-level randomization in a marketplace or social product.
- Remedies: cluster or geo randomization, switchback tests.

**I4. Novelty effects and long-term effects are examined.**
- Mistakes: a 1-week test for a change with a learning curve.
- Remedies: a longer test, a long-term holdout.

**I5. The rollout has a ramp with a shadow or canary stage.**
- Mistakes: 0% to 100% in one step.
- Remedies: shadow, then 1%, 5%, 25%, 50%, 100%, each with a gate. When
  the quality is partly subjective (the user experience), add an internal
  or opt-in stage before the random ramp: collect feedback and test the
  guardrails.

**I6 [C]. The fallback has a trigger and a target, and there is a kill
switch.**
- Mistakes: no fallback, or "we will roll back" with no trigger.
- Remedies: a named trigger (error rate, latency, metric drop), a named
  target (previous model or heuristic), and a switch that works without a
  deploy.

**I7. Monitoring covers system health, predictions, drift, and delayed
performance.**
- Mistakes: system health only.
- Remedies: latency and errors, the score distribution, feature drift
  (PSI), and the model metric when the labels arrive.

**I8. Each monitored item has a threshold and an owner.**
- Mistakes: dashboards with no alerts.
- Remedies: an alert threshold and an on-call owner for each item.

**I9. There is a runbook for retraining and rollback.**
- Mistakes: the procedure exists only in one person's head.
- Remedies: a written runbook with the commands.

**I10. There is a test plan and CI/CD.**
- Mistakes: no unit or integration tests for the feature code. No load
  test, or a load test at the average load. Manual deploys.
- Remedies: unit tests for the feature and scoring code, an integration
  test of the full path, a load test at the peak QPS with the planned
  replicas (or the batch job inside its window), and a CI/CD pipeline
  with the promotion gate from F5.

**I11. The execution plan is realistic.**
- Mistakes: no milestones, or milestones with no dates. No team process.
- Remedies: epics or milestones with dates and owners, and the team
  process (sprint length, review cadence). Check it against H4.

## J. Post-delivery and responsible ML

**J1. There is a plan to analyze the results by segment.**
- Mistakes: only the average effect.
- Remedies: effects for each segment and heterogeneous treatment effects.

**J2. There is explainability where it is necessary.**
- Mistakes: a black-box score for a decision that users or regulators
  question.
- Remedies: SHAP reason codes, a simpler model for regulated decisions.

**J3. There are fairness and bias checks.**
- Mistakes: no slices by protected or sensitive groups.
- Remedies: metric parity checks for each group, with a threshold.

**J4. There is a plan for abuse and adversarial attacks.**
- Mistakes: a system that users can game, with no plan.
- Remedies: abuse monitoring, rate limits, robust features.

**J5. The next-version plan uses the launch data.**
- Mistakes: a roadmap fixed before the launch.
- Remedies: name the questions that the launch will answer, and the
  decisions that depend on them.

**J6. Reusable components are named.**
- Mistakes: features, models, or pipeline parts that only this team uses,
  when other teams need the same thing.
- Remedies: name each reusable component (features, architecture,
  platform part) and the team that can reuse it.

## K. Cross-section consistency

**K1 [C]. The goal, the primary metric, the evaluation metric, and the A/B
metric form one chain.**
- Mistakes: the PRD says retention, the evaluation reports AUC, the A/B
  test measures clicks.
- Remedies: write the chain in one line, and fix each break.

**K2. The framing sources and the architecture sources are the same.**
- Mistakes: the framing names a table that the architecture does not
  read.
- Remedies: one list of sources, used by both sections.

**K3. The model class in the phasing agrees with the deep dive.**
- Mistakes: the phasing says GBDT for V1, the deep dive says a DNN.
- Remedies: align them, or record the change with a reason.
