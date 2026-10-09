---
name: ml-modeling-serve
description: >-
  Use to design and measure how an evaluated model is served - batch or
  online mode, a serve.py scoring function that reuses the training feature
  code, measured p50/p99 latency and throughput, capacity for the peak load
  (replicas or batch window), and cost. Step 5 (final) of the ml-modeling-*
  chain (data → features → train → evaluate → serve). Trigger on "how do we
  serve this model," "measure inference latency," "how many replicas," or
  continuing modeling work in an existing ML project folder.
---

# Serve

Contents: Steps | Mode | serve.py | Measure | Capacity and cost | Output |
Check | After this step

The hands-on version of the Serving item in `ml-system-design-deep-dive`.
Both routes give `ml-system-design-delivery` the same serving facts.
Reason: `../adr/0013-serving-on-both-routes.md`.

- **Reads:** the PRD non-functional requirements in
  `<project-folder>/prd/<topic>.md` (peak load, p99 latency,
  availability, cost sensitivity); the framing and the online diagram in
  `design/high-level.md` (scoring population and cadence);
  `modeling/04-evaluate.json` (`verdict_status`).
- **Loads:** `modeling/model.joblib` and `transform()` from
  `modeling/features.py` (see "Handoff" in `../ml-modeling/SKILL.md`).
- **Measures on:** `01-data.json` -> `dataset.test` (the input rows, not
  the labels).
- **Writes:** `modeling/serve.py`, `modeling/05-serve.md`,
  `modeling/05-serve.json`.
- **Reference:** `../ml-serving.md` (mode rule, latency budget, capacity
  formula, cost, what to record).
- **Rules:** `../ml-system-design/SKILL.md`, "Project folder", "Output
  docs", "Check the output", "Skill improvement log".
- Not in monkey-mode. No dashboard change: the dashboard shows EDA and
  final results only (`../adr/0002-modeling-dashboard.md`).

## Steps

Progress (copy into your reply, tick each line):

```
[ ] 1 Design docs changed?
[ ] 2 Evaluate verdict
[ ] 3 Mode, stages, latency budget
[ ] 4 serve.py
[ ] 5 Measure (bench_serve.py)
[ ] 6 Capacity and cost
[ ] 7 Write 05-serve.md and .json
[ ] 8 Check
```

1. Run "Design docs changed?" in `../ml-modeling/SKILL.md`.
2. Read `verdict_status` in `04-evaluate.json`. On `fail`, Regular asks
   the user before going on (serving a model that misses the bar is often
   wasted work). Quick POC goes on and says so in `05-serve.md`.
3. Pick the mode from the scoring cadence (`../ml-serving.md`, "Mode"),
   with the reason. Name the stages and the candidates at each stage.
   Divide the PRD p99 into a budget for each stage.
4. Write `serve.py` (below).
5. Measure (below).
6. Compute capacity and cost (below).
7. Write the output.
8. Check.

## Mode

- **Regular:** all steps. Ask when the PRD has no peak load or p99.
- **Quick POC:** steps 1-5 in full. For step 6, a one-line capacity
  estimate. Missing PRD numbers become marked assumptions.

## serve.py

`modeling/serve.py` defines `score(df) -> scores`, one score per row of
raw input (the columns of `dataset.test` without the label):
- load `model.joblib` once, at import;
- call `transform(df)` from `features.py`, then the model;
- return probabilities or values. Apply the saved threshold only if the
  consumer needs a decision.

One code path for training and serving prevents training-serving skew. Do
not copy the feature logic into `serve.py`. If `transform()` loads history
or lookup tables, cache them once per process inside the feature module
(for example `functools.lru_cache`), then check that serving scores equal
the evaluate scores.

## Measure

Run the bundled script. Timing by hand is easy to get wrong (no warm-up,
the mean in place of p99, 1 row timed as a batch):

```
uv run python3 .agents/skills/personal/ml-modeling-serve/scripts/bench_serve.py \
  --serve <project-folder>/modeling/serve.py \
  --rows <dataset.test path> --model <project-folder>/modeling/model.joblib \
  --out <project-folder>/modeling/05-bench.json
```

It prints p50/p95/p99 for single-row requests, the QPS of 1 worker, batch
rows per second, the model size, and the machine. Compare the p99 with the
ranking or scoring stage budget from step 3. The laptop is not the
production machine: say so next to the numbers.

**Batch mode:** add `--full` (and `--chunk N` if the job scores in
chunks). It scores the whole table in file order, as the batch job does,
and reports `full_batch.rows_per_sec`. Use that number as
`batch_rows_per_sec` in `05-serve.json`. The random 1,000-row batches pay
any fixed cost per call 1,000 times, so they can understate a batch job by
100x or more.

## Capacity and cost

Use the formulas in `../ml-serving.md`, "Scaling" and "Cost":
- **Online:** replicas from the peak QPS (not the average), the cache hit
  rate, the measured QPS per worker, and headroom 1.3-1.5. Name the
  degradation order under overload.
- **Batch:** job time = scoring population / measured rows per second.
  Compare it with the scoring window.
- **Cost:** per 1,000 predictions and per day at peak (online), or per run
  (batch). Unknown prices: the formula, and the result marked as an
  assumption.

## Output

`05-serve.md` has one heading for each item in "What to record" in
`../ml-serving.md`, plus the measured numbers and a verdict: meets or
misses the p99 target, and why.

`05-serve.json` (`ml-system-design-delivery` reads it):

```json
{
  "mode": "batch | online | hybrid",
  "mode_reason": "<cadence>",
  "p50_ms": 0.0, "p99_ms": 0.0, "p99_target_ms": 0.0,
  "meets_latency_target": true,
  "batch_rows_per_sec": 0.0, "model_mb": 0.0,
  "peak_qps": 0, "qps_per_replica": 0.0, "replicas": 0,
  "batch_minutes": null, "scoring_window_minutes": null,
  "cost_per_1k": null, "cost_per_day": null,
  "assumptions": ["<each assumed number>"]
}
```

## Check

Do "Check the output" in `../ml-system-design/SKILL.md`. Intent questions:
1. Are the latency and throughput numbers from `bench_serve.py` on
   `serve.py`, not guessed?
2. Does `serve.py` call `transform()` from `features.py`, with no copied
   feature logic?
3. Is the p99 compared with the PRD target (or the stage budget), with a
   plain verdict?
4. Is the capacity computed from the peak QPS (or the batch window), with
   the math shown? Is the mode reason tied to the cadence?

Done when the 4 answers are yes, `check_doc.py` prints `OK`, and
`05-serve.json` matches `05-serve.md`.

## After this step

- `ml-system-design-delivery`: its Deployment load test uses `peak_qps`
  and `replicas` from `05-serve.json` as the pass target.
- `ml-modeling-autoresearch` can promote a new model. Then `05-serve.*`
  is stale: run this step again.
- To ship: give `04-evaluate.md` and `05-serve.md` to the `implement`
  skill.
