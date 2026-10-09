# ML System Design Template

Contents:
1. Definition: Problem, Requirements, Baseline, Metrics, Team
2. High-level Design: ML framing, Architecture, Delivery phases
3. Design Deep Dive: Data, Features, Models, Training, Serving
4. Delivery: Fallback, Execution, Deployment, Evaluation, Monitoring,
   Retraining
5. Post Delivery: Analysis, Explainability, Iteration, Democratize

```
1 Definition -> 2 High-level -> 3 Deep dive -> 4 Delivery -> 5 Post delivery
(why, what,     (framing,       (data,         (ship, run,   (learn, grow)
 who)            architecture)   model,         protect)
                                 serving)
```

Each section is one `ml-system-design-*` skill. The skills use the 3
principles in `.agents/skills/personal/ml-design-principles.md`:
1. Simple by default. Complex only with evidence.
2. The objective is the intended behavior, not the metric.
3. A proven version ships, and it keeps up with change.

Never skip these 3 items: out-of-scope, the baseline, and the fallback.

---

## 1. Definition

This section sets the context: the why, what, and who of the project. Do
it before the technical design starts.

### Problem

The most important part. It gives the business and user context.
- Define the core problem that the project solves.
- Say why the project is important now.
- Name the user pain point that it fixes.
- Show how it aligns with the company goals: this quarter (short term)
  and the 3-year strategy (long term).
- Name the event to predict in business terms: what happens, to whom, by
  when.

### Requirements

The scope and the constraints of the system.
- Features: the capabilities that the system must have. Example: "must
  rank a list of items".
- Out-of-scope: what this version does not include. Example: "no
  real-time personalization in V1".
- Non-functional:
  - Scale: the peak load, not the average. Example: "10 million requests
    per minute at peak".
  - Latency. Example: "p99 latency under 100 ms".
  - Availability. Example: "99.99% availability".
  - Explainability: hard (each decision needs a reason) or soft.
  - Cost sensitivity: an exact budget, low, medium, high, or unknown.

### Baseline

The simple approach that the ML system must beat. It is often not ML.
- Status quo: what users do today without the system.
- Recommended baseline: one strong simple rule. Example: "most popular
  items in the last 7 days".
- Floor: the most naive version (random, majority class, global
  popularity). It shows if the metric means anything.
- Build decision: now, later, or never.

### Metrics

How you measure success.
- Offline: metrics on a static dataset. One primary metric, with a
  threshold. Examples: AUC, nDCG, precision, recall.
- Online: the business effect in a live A/B test. Examples: CTR,
  conversion rate, session time.
- Guardrails: metrics that must not get worse.
- Intended behavior (Principle 2):
  - Write what the model must do, in user terms, in one or two lines.
  - List the ways the model can game the primary metric. Example: "it
    shows the same popular items to all users". Give each one a
    guardrail or an output check.
  - If the goal is a target level and not a maximum, say so. Example: "a
    share of new items of at least 10%".

### Team

The people of the project.
- Stakeholders: the people to keep informed. Example: a Director of
  Product.
- Collaborators: the teams that you work with each day.
- Dependencies: the work that you need from other teams, and the work
  that other teams need from you. Example: "blocked until the Data
  Platform team gives access to the new user logs".
- Reuse: existing components or platforms to reuse, and the downstream
  users of the output.

---

## 2. High-level Design

The technical strategy and the roadmap.

### ML framing

Change the business problem into a precise ML problem. Example: "show
users better content" becomes learning-to-rank on the click probability
of each item. For each model, give:
- the prediction target;
- the label definition and horizon;
- the scoring population and cadence (who gets a score, and when);
- the unit of prediction (what one row is);
- the known exclusions or contamination.

One model for each project folder.

### Architecture

Make 2 separate diagrams. Name the real sources ("user data" is not a
source).
- Online inference: the request and response path. For a batch-only
  system: scheduled job, then scores, then the consumer.
- Offline training: source tables or logs, then processing, then
  training.

### Delivery phases

Divide the project into crawl, walk, run (V0, V1, V2). For each phase,
give:
- the features, the model class, and its architecture family;
- a rough timeline and the number of team members;
- the expected gain over the baseline, which pays for the added
  complexity (Principle 1);
- the gate to the next phase: the metric, the stability across seeds or
  retrains, the segment and edge-case coverage, and the running cost
  (Principle 3).

V0 is the recommended baseline, or the doc says why not.

If a committed date depends on a method that is not proven on this
problem, keep the last proven phase shippable and improving. Name the
date and the evidence that decide which version ships (Principle 3).

---

## 3. Design Deep Dive

The technical core of the design. The hands-on `ml-modeling-*` chain
answers the same 5 items with real data.

### Data

- Online: the data that real-time inference needs.
- Offline: the data that batch training needs.
- Data engineering: the new work. Example: "an ETL job that joins the
  impression logs and the conversion logs".

### Features

- A concrete list: user, item, and context features.
- Each difficult transform. Example: embeddings for a high-cardinality
  `user_id`.

### Models

- The candidates, always with the simplest option that can work.
  Examples: logistic regression, GBDT, a deep neural network.
- The architecture, and why. Example: two-tower retrieval, then a GBDT
  ranker.
- The trade-offs: performance, running cost, maintenance cost,
  explainability.
- The model for each phase. A more complex candidate wins only if it
  passes the complexity gate: fill the cost table (Principle 1).

### Training

- Loss function: what the training optimizes.
- Algorithm and labels: how you get the ground truth.
- Sampling: the class imbalance, and the negatives if the logs hold only
  positives (types, ratio, correction).
- Setup: the key hyperparameters, the hardware, and the training time.
- Retraining (Principle 3): the retrain time and cost, compared with the
  cadence of scheduled upstream changes. One retrain must fit inside one
  change cycle. Example: "one retrain takes 4 hours; the catalog changes
  each week".

### Serving

- Mode: batch (scores computed in advance) or online (scores for each
  request), with the reason.
- Latency: divide the p99 target from section 1 into a budget for each
  stage. Example: retrieval, then ranking.
- Features online: fetched with the same code as in training.
- Capacity: the replicas for the peak QPS, or the batch job time against
  its window.
- Cost: the hardware (CPU or GPU) and the cost at peak load.

---

## 4. Delivery

How the system goes to production, and how it keeps running.

### Fallback

Do this first: reviews skip it most often. A doc without a fallback is
not complete.
- What happens when the new model fails or gets worse.
- The target: the previous model, or the recommended baseline.
- The trigger. Example: "error rate over 1% for 5 minutes".
- A kill switch.

### Execution

- Epics or milestones, each with a date. This plan has more detail than
  the delivery phases.
- The team process. Example: "two-week sprints, with a stakeholder
  review each week".

### Deployment, rollout, and testing

- Rollout: shadow, then a ramp, each stage with a gate. Example: "1%,
  5%, 25%, 50%, 100% over two weeks".
- When the quality is partly subjective, start with an internal or
  opt-in group. It collects feedback and tests the guardrails
  (Principle 3).
- Testing: unit, integration, and load tests. The load test runs at the
  peak QPS, with the capacity from Serving.
- CI/CD.

### Evaluation

This part adds detail to the Metrics of section 1.
- Online: the A/B test design: the metric, the randomization unit, the
  duration or power, and the significance method.
- Offline: the method. Example: "a held-out test set from the last 7
  days".
- Output review (Principle 2): read the top outputs for typical and
  edge-case inputs (new users, rare segments, empty history). Name each
  degenerate pattern.

### Monitoring

The live dashboards after launch. Each metric has a threshold.
- System health: latency, error rate. Start from the stage budgets in
  Serving.
- Model health: the prediction distribution, feature drift.

### Retraining

- Triggers: drift, and each scheduled upstream change (Principle 3).
- The owner after launch.
- The runbook. The owner runs it without the authors of the model.

---

## 5. Post Delivery

The life of the project after a successful launch.

### Analysis

- How you analyze the results after the A/B test ends.
- The deep-dive plan: why a result occurred, not only what occurred.

### Explainability

- How model decisions become clear to people. Example: SHAP or LIME for
  each prediction.
- This helps debugging, and it builds trust with stakeholders.

### Iteration

- The next versions (V2, V3), based on the analysis.

### Democratize

- The components that other teams can reuse: features, the model
  architecture, platform parts.
- Name the team and the component.
