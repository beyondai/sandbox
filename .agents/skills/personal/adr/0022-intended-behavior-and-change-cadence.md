# Principle 2 (the intended behavior, not the metric), retrain cadence, fuller phase gates

## Context

On 2026-10-09 the user gave notes from a conference talk about taking an
ML system from research to a live product with frequent releases. The
user asked which lessons help the `ml-*` and `ml-critique*` skills, with
no names of people or companies, and with the lessons stated for general
ML products.

The skills already covered most lessons: a simple baseline first, a
fallback with a kill switch, seed variance, a rollout ramp, a retrain
trigger, reuse, and cost. 4 lessons were new or only partly covered:
1. The optimizer improves the metric, not the intent. A model can game
   its metric with degenerate outputs. B6 (counter-metrics) covered side
   effects, not the model itself exploiting the metric.
2. Scheduled upstream changes (releases, catalog or rule updates) break a
   model on a known cadence. F5 had only a drift trigger, and no check
   that one retrain fits inside one change cycle.
3. Phase gates checked only the metric, not the stability, the coverage,
   or the cost. The rollout had no internal or opt-in stage for quality
   that is partly subjective.
4. A committed launch date could depend on an unproven method, with no
   proven version kept ready to ship.

## Decision

- New Principle 2 in `ml-design-principles.md`: write the intended
  behavior; list the ways the model can game the metric, each with a
  guardrail or an output check; read a sample of outputs before launch;
  optimize to a target level when the goal is not a maximum.
- New catalog items: system B7 [C] (ways to game the metric), system F7
  (retraining fits the cadence of scheduled changes), modeling I12
  (output sample review).
- Extended remedies: system H2 (the gate checks stability, coverage, and
  cost), H3 (keep the last proven version shippable), I5 (an internal or
  opt-in stage).
- Pointers in `ml-system-design-definition`, `ml-system-design-high-level`,
  `ml-system-design-deep-dive`, `ml-system-design-delivery`, and
  `ml-modeling-evaluate`. Coverage map rows for B7, F7, and I12.
- The skill text uses general ML words only. "Game the metric" is the one
  term for metric gaming.

## Consequences

- A Definition has one more item, and the evaluate step has one more
  required check (an output review with about 10 typical and 10
  edge-case inputs).
- A design that names no ways to game its metric can get a P1 or P2
  (B7 is a classic-mistake item).
- Eval specs do not test the new items. They are not run yet (evals on
  hold for token cost).
