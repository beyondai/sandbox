# ML design and review principles

Contents: Summary | Principle 1, simple by default (Rule | The cost table |
Budgets in the PRD | Why | How each skill uses this principle) | Principle 2,
the intended behavior, not the metric (Rule | Why | How each skill uses this
principle) | Principle 3, a proven version ships, and it keeps up with
change (Rule | Why | How each skill uses this principle)

This file is the single source of truth for the principles that the `ml-*`
skills use to design and to review ML systems. The design skills apply them
when they write. The `ml-critique` skills judge write-ups against them.

To add a principle, give it a number, a one-line rule, the full text, the
reason, and how each skill uses it. Then add a pointer in each skill that
uses it.

## Summary

| # | Principle | Main checks |
|---|---|---|
| 1 | Simple by default. Complex only with evidence. | complexity gate, cost table |
| 2 | The objective is the intended behavior, not the metric. | ways to game the metric, output review |
| 3 | A proven version ships, and it keeps up with change. | full phase gates, proven fallback version, staged rollout, retrain cadence |

---

## Principle 1: Simple by default. Complex only with evidence.

```
   rule / heuristic ---> linear / GBDT ---> complex model or system
                    ^                   ^
                    |                   |
              each step must pass the complexity gate:
              1. gain > noise
              2. value of the gain > added total cost
                 (running + maintenance + explainability + risk)
              3. compared with a fairly tuned simpler option
```

### Rule

1. Start with the simplest method that can work: a rule or heuristic, then
   a linear model or GBDT.
2. Complexity includes the model, the features, the data dependencies, the
   pipeline stages, and the serving infrastructure. Apply this principle to
   all of them, not only to the model.
3. Add complexity only when it passes the **complexity gate**:
   1. The gain is larger than the noise (a confidence interval, or the
      variance across seeds or folds).
   2. The business value of the gain is larger than the added total cost.
      Use the cost table below.
   3. The comparison is with a fairly tuned simpler option: the same
      features, the same split, and the same tuning budget.
4. Each added component must earn its place. Show it with an ablation:
   remove the component and measure the loss.
5. Fix the data and the labels before you add model complexity. Better
   labels and features usually give more, at a lower cost.
6. Keep the simple model. It is the baseline for each later version and the
   fallback in production.
7. The context sets the weight of explainability:
   - Hard requirement: regulated decisions, and decisions that users or
     operators must understand or dispute.
   - Soft factor: internal ranking, and decisions with a cheap error.
8. When the standard method for a problem type is complex (images, text,
   audio, retrieval from a large catalog), use it. Still compare it with a
   simple baseline. This principle is not a rule against complex methods.
   It is a rule that each complex method must show its value.

### The cost table

Use this table to compare each more complex option with the simpler option.
Give rough values. "Unknown" is a valid value, but state it.

| Factor | What to estimate |
|---|---|
| Value of the gain | The metric gain, converted to business value where possible (for example, users retained, revenue, hours saved). |
| Running cost | Training compute, serving compute (GPU or CPU), latency, storage. |
| Maintenance cost | New pipelines, data dependencies, retraining effort, on-call load, team skills that are necessary. |
| Explainability | Can the team explain a single prediction? Is it a requirement in this context? |
| Risk | Failure modes, debug difficulty, vendor or framework lock-in, time to deliver. |

A decision is a judgment, not a fixed ratio. Write the table, then write one
line: why the value is larger (or not larger) than the added cost.

### Budgets in the PRD

The PRD records the explainability need and the cost sensitivity as
non-functional requirements. An exact cost limit is often not available.
These forms are all valid:

- An exact budget (for example, "$2k per month serving").
- A relative level: cost sensitivity `low`, `medium`, or `high`.
- `unknown`. The gate then compares the options relative to each other, and
  the critique asks the question.

### Why

- Most of the cost of an ML system is outside the model code: data
  dependencies, pipelines, monitoring, and configuration (Sculley et al.,
  "Hidden Technical Debt in Machine Learning Systems", 2015).
- A simple first launch gets the pipeline, the metrics, and the feedback
  working. Most early gains come from data and features, not from the model
  ("Rules of ML", Google, rules 1, 4, and 17).
- A complex model that wins against an untuned simple model proves nothing.
  A small gain inside the noise is not a gain.

### How each skill uses this principle

| Skill | Use |
|---|---|
| `ml-system-design-definition` | Records the explainability need and the cost sensitivity in the non-functional requirements. |
| `ml-system-design-high-level` | Phasing: V0 is a rule or a simple model. Each later phase names the gain that justifies its added complexity. |
| `ml-system-design-deep-dive` | Models: compares each candidate with the simplest option, with the cost table. |
| `ml-modeling-train` | Starts simple. Selects a more complex model only if it passes the gate. Writes the cost table in `03-train.md`. |
| `ml-modeling-multiagent` | Always includes a simple candidate. Selects the simplest candidate inside the noise of the best, unless a more complex one passes the gate. |
| `ml-critique` and lenses | No simple baseline: P1. Complexity that does not pass the gate: P2. |

---

## Principle 2: The objective is the intended behavior, not the metric.

```
   intended behavior ---> primary metric ---> optimizer
          ^                                       |
          |      the optimizer finds outputs      |
          +---- that score well but miss the  <---+
                 intent: name them, check them
```

### Rule

1. Write the intended behavior in one or two lines, next to the primary
   metric. It is what the product needs the model to do, in user terms.
2. List the ways the model can game the primary metric: outputs that
   score well and still miss the intent. Examples: the same popular items
   for every user, repeat loops, clickbait, near-duplicate results, a
   score that stays high because the model avoids hard cases.
3. Give each item a guardrail metric or an output check. A counter-metric
   for a side effect is not enough when the model itself exploits the
   metric.
4. Before launch, a person reads a sample of outputs: typical inputs and
   edge-case inputs (new users, rare segments, empty history). Reason:
   aggregate metrics hide degenerate outputs.
5. When the goal is a target level and not a maximum, say so and optimize
   to the target. Examples: a difficulty or price matched to the user, a
   diversity floor, a share of new items.

### Why

- An optimizer improves the number it gets, not the intent behind it.
  The stronger the optimizer, the more it finds the gaps between the two.
- A model with the best offline score can still harm the user experience,
  and the users leave before the long-term metrics show it.

### How each skill uses this principle

| Skill | Use |
|---|---|
| `ml-system-design-definition` | Success metrics: states the intended behavior, and lists the ways the model can game the primary metric, each with a guardrail. |
| `ml-system-design-prd` | Asks for the intended behavior in the interview (a Definition branch), and checks that each way to game the metric has a guardrail. |
| `ml-modeling-evaluate` | Output review: reads a sample of top outputs for typical and edge-case inputs, and reports the degenerate patterns. |
| `ml-critique` and lenses | System B7 `[C]`: no named ways to game the metric, or no check for each. Modeling I12: no output sample was read. |

---

## Principle 3: A proven version ships, and it keeps up with change.

```
   V0 (proven) --gate--> V1 --gate--> V2 ...      gate = metric + stability
        |                 |                              + coverage + cost
        +-- stays shippable until the next version passes its gate
                              |
   internal / opt-in --> shadow --> 1% --> ... --> 100%   (staged rollout)
                              |
   scheduled changes (releases, catalog, rules) --> retrain, inside one cycle
```

### Rule

1. A phase gate checks more than the metric: the stability across seeds
   or retrains, the coverage of segments and edge cases, and the running
   cost. Reason: a metric gain that is unstable, narrow, or too costly
   fails in production.
2. Keep the last proven version (the baseline or the previous phase)
   shippable, and keep improving it, while a new method is tested. If a
   committed date depends on a method not yet shown to work on this
   problem, name the date and the evidence that decide which version
   ships.
3. Roll out in stages, each with a gate: shadow, then a small random
   share, then more. When the quality is partly subjective (the user
   experience), put an internal or opt-in stage first: it collects
   feedback and tests the guardrails.
4. List the scheduled upstream changes (product releases, catalog or rule
   updates, pricing or policy changes) and their cadence. One retrain
   must fit inside one change cycle, in time and in cost. Each scheduled
   change is a retrain or re-check trigger, next to the drift trigger.
5. Name the owner after launch. The owner runs the retrain from a
   runbook, without the authors of the model.

### Why

- A launch that depends on an unproven method has no plan B. A proven
  version that keeps improving is the plan B, and often it is enough.
- Most production breaks come from known changes on a known schedule,
  not only from slow drift. A model that takes longer to retrain than one
  change cycle is always out of date.
- Offline metrics do not show all user-facing quality. A small internal
  or opt-in group finds the problems before random users do.

### How each skill uses this principle

| Skill | Use |
|---|---|
| `ml-system-design-high-level` | Phasing: each gate checks the metric, the stability, the coverage, and the cost. The last proven phase stays shippable when a date depends on an unproven method. |
| `ml-system-design-deep-dive` | Training: compares the retrain time and cost with the cadence of scheduled changes. |
| `ml-system-design-delivery` | Deployment: an internal or opt-in stage before the random ramp for partly subjective quality. Monitoring: the retrain triggers, the owner, and the runbook. |
| `ml-critique` and lenses | System H2 (full gates), H3 (proven version shippable), I5 (staged rollout), F7 (retrain cadence, owner). |
