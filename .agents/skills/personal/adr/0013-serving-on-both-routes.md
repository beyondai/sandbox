# Serving is a design item on both routes

## Context

The user added a "Serving" sub-section to section 3 (Deep Dive) of
`docs/ml-design-template.txt` on 2026-10-09: mode, latency, scaling, and
cost. The skills had 4 gaps:

- **No skill wrote serving.** `ml-critique-system` already checked it
  (C3, C4, C5, F3, F4), so a doc could fail checks that no skill asked it
  to pass.
- **The 2 routes gave delivery different inputs.** ADR 0006 says that
  deep-dive and `ml-modeling-*` answer the same 4 questions. If only
  deep-dive covers serving, delivery gets serving facts on the paper
  route only.
- **Nothing checked scaling.** The PRD gave a load. No item turned it
  into a capacity plan, and no test proved it.
- **No measured latency.** The hands-on route had a real model but never
  timed it.

## Decision

```
prd -> high-level -> [ deep-dive: data, features, models, training, SERVING ]
                     [ mm: data -> features -> train -> evaluate -> SERVE   ] -> delivery
                                                                  05-serve.*     (same facts
                     shared reference: ml-serving.md                              on both)
```

1. **Both routes answer 5 items.** Deep-dive adds a Serving item. The
   hands-on chain adds step 5, `ml-modeling-serve`, after evaluate (user
   decision: "if the deep-dive branch covers serving, the ml- branch
   should cover it too").
2. **One shared reference, `ml-serving.md`.** Mode by cadence, stages,
   latency budget, online features, hardware, caching, the capacity
   formula, cost, and "What to record". Same pattern as
   `ml-model-training.md` (ADR 0012).
3. **Measured, not guessed, on the hands-on route.** `serve.py` wraps
   `transform()` and the model (one code path, no skew).
   `scripts/bench_serve.py` times it: warm-up, single-request p50/p99,
   batch rows per second, model size. A script, because timing by hand is
   fragile (ADR 0011, guide 3).
4. **Scaling from requirement to proof.**
   - Definition asks for the peak load, not the average.
   - Serving computes replicas from the peak QPS with headroom, or the
     batch time against the window.
   - Delivery's load test uses that target.
   - Critique checks it: system F4a, modeling K4.
5. **Delivery cites, does not redesign.** It reads Serving from
   `05-serve.md` or `design/deep-dive.md`, like its Eval item.

## Consequences

- The chain has 5 steps. "full chain" and "run all steps" run all 5.
- After autoresearch promotes a model, `05-serve.*` is stale. The
  autoresearch report says so; it does not run serve (write boundary).
- The dashboard does not show serving (ADR 0002 keeps it small).
- ADR 0006 still says "four questions". It is a historical record, so it
  stays as written. This ADR updates it.
- Laptop numbers are not production numbers. `05-serve.md` names the
  machine.
- Step 3 gets an early latency filter. Both `ml-modeling-train` and
  `ml-modeling-multiagent` record a rough 1-row predict time for each
  candidate, so a winner that cannot meet the PRD p99 is found before
  step 5.
- `ml-modeling-multiagent` now saves `model.joblib` (the winner, refit,
  with its out-of-fold threshold). Before, only `ml-modeling-train` did,
  so the parallel route could not reach evaluate or serve without a
  manual step.
