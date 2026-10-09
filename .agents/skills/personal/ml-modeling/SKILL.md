---
name: ml-modeling
description: >-
  Use when executing the hands-on ML modeling workflow for a project that
  already has a PRD and a fork-grade `design/high-level.md` - building the
  labeled table, profiling data, engineering features, training a model,
  evaluating it, and measuring how it serves. The hands-on alternative to
  ml-system-design-deep-dive. Entry point for the whole data-to-served-model
  chain; for one step only,
  trigger that step's own skill directly instead. Trigger on "let's
  build/train/prototype a model for X," "quick ML POC," or continuing modeling
  work in an existing ML project folder.
---

# ML Modeling

Contents: Steps | Required upstream | Modes | Dashboard | Bundled tools | After
step 5 | Check

5 steps. Each step is its own skill. Files in `<project-folder>/modeling/`
connect the steps, not the conversation, so each step can run alone in a
new session.

| Step | Skill | Writes |
|---|---|---|
| 1 | `ml-modeling-data`: build or register the labeled table, profile, clean | `01-data.md`, `01-data.json` |
| 2 | `ml-modeling-features` | `02-features.md` |
| 3 | `ml-modeling-train` (sequential) or `ml-modeling-multiagent` (parallel) | `03-train.md` |
| 4 | `ml-modeling-evaluate` | `04-evaluate.md`, `04-evaluate.json` |
| 5 | `ml-modeling-serve`: mode, `serve.py`, measured latency, capacity | `05-serve.md`, `05-serve.json` |

- The `dataset` block in `01-data.json` is the data contract. Later steps
  read table paths, the label, and the split roles from it, never from
  prose.
- One model for each project folder.

## Steps

Progress (copy into your reply, tick each line):

```
[ ] 0 PRD and high-level exist; spec exists or is synthesized
[ ] 1 data   [ ] 2 features   [ ] 3 train   [ ] 4 evaluate   [ ] 5 serve
[ ] Check each step's output (see the Check step in each skill)
```

1. `/ml-modeling <topic>` runs step 1, reports the result, and stops for
   the user's confirmation. Then step 2, and so on.
2. Run all 5 steps without stops only when the user says so ("full
   chain", "run all steps", "don't stop between steps").
3. For one step, run that skill. It continues from the files that exist.

Project folder, output format, the Check procedure, and the skill
improvement log: `../ml-system-design/SKILL.md`, sections "Project
folder", "Output docs", "Check the output", and "Skill improvement log".

## Required upstream

Each step reads `<project-folder>/prd/<topic>.md` and
`<project-folder>/design/high-level.md`, in both modes. If one is missing,
do not make a substitute. Run `/ml-system-design-prd` and
`/ml-system-design-high-level` first (POC mode for speed).

The ML framing in high-level must be fork-grade. For each model it gives:
the prediction target, the label definition and horizon, the scoring
population and cadence, the unit of prediction, and the known exclusions.
Its Architecture diagram names the source tables.

`ml-modeling-*` is the hands-on version of the deep dive. It does not read
`design/deep-dive.md`. If a project has both, delivery uses the newer one.
Reason: `../adr/0006-fork-after-high-level.md`.

What each step reads, and what it decides:

- **`ml-modeling-data`.** Reads the framing, the Architecture source
  tables, and the PRD scope. Decides the split, the cutoffs, and which
  quality flags to clean. Records them in the `dataset` block of
  `01-data.json`, with the reasons in `01-data.md`.
- **`ml-modeling-features`.** Reads the framing (population, unit) and
  `01-data.md`. Decides the feature list (`02-features.md`).
- **`ml-modeling-train` / `-multiagent`.** Reads the Phasing (model class
  for each phase), the algorithm-selection matrix, and the class balance
  in `01-data`. Decides the candidates, the loss, and the class weights
  (`03-train.md`).
- **`ml-modeling-evaluate`.** Reads the PRD offline metrics (primary,
  secondary, guardrails) and `dataset.split`. Writes `04-evaluate.md` and
  `.json`.
- **`ml-modeling-serve`.** Reads the PRD non-functional requirements
  (peak load, p99, cost sensitivity), the scoring cadence in the framing,
  and `04-evaluate.json`. Decides the serving mode and the capacity
  (`05-serve.md` and `.json`). Same items as the deep-dive Serving item.

Handoff between steps 2 to 5 (so evaluate never refits on test, and
serving uses the training feature code):
- Features writes `modeling/features.py` with `transform(df)`, fit on
  train only. The same function transforms train and test.
- Train saves `modeling/model.joblib`: the fitted model and its decision
  threshold.
- Evaluate loads both, scores `dataset.test` once, and saves the per-row
  scores to `modeling/test_scores.csv`. A metric change then reruns only
  the metric code.
- Serve writes `modeling/serve.py` with `score(df)`: it calls
  `transform()` and the model from `model.joblib`. No copied feature
  logic.

### The spec

The first step that runs without `spec/<topic>.md` synthesizes it from
`prd/`, `adr/`, and `design/high-level.md`. Each section is a summary, not
a copy. The first 2 lines hold the hashes from `git hash-object -w <file>`.
The `-w` stores the blob, so `git diff` works for an uncommitted version.

```
prd-hash: <sha>
high-level-hash: <sha>

# Spec: <topic>
## Problem Statement      <- PRD Problem, one paragraph
## Solution               <- high-level ML framing (target, label, horizon,
                             population, unit, exclusions) + which model this
                             folder builds + the offline/batch architecture
## Implementation Decisions
                          <- high-level Phasing (model class per phase),
                             Architecture's source tables, every adr/ decision
                             in one line each
## Testing Decisions      <- PRD Metrics - offline (primary, secondary,
                             guardrails); split rule once mm-data has set it
## Out of Scope           <- PRD Requirements - scope, out-of-scope list
```

Reasons: `../adr/0001-ml-modeling-family-and-continuity.md`,
`../adr/0006-fork-after-high-level.md`.

### Design docs changed?

Each step runs this check first, in both modes:

1. Run the script:

   ```
   bash .agents/skills/personal/ml-modeling/scripts/spec_hash_check.sh <project-folder>
   ```

2. `MATCH`: continue, and say nothing. Exit 2 with "no spec/":
   synthesize the spec first (below), then run the script again.
   `NOHASH` or `MISSING`: stop and ask the user.
3. `CHANGED <file>`: the script prints `OLD <sha> NEW <sha>`. Run `git
   -C <project-folder> diff <old> <new>`, and summarize which sections
   changed. Then ask 2
   questions before the step:
   - Synthesize `spec/<topic>.md` again now, or keep the current spec?
   - Apply the changed decisions in this step and later, or continue with
     the earlier decisions?
4. Record the answer as one line in the step's output `.md`. Example:
   `high-level changed since spec (ML framing); user chose: apply going
   forward, spec kept`.
5. If the spec was synthesized again, or the user chose "apply", run the
   script with `--refresh prd` or `--refresh high-level`. If the user
   chose the earlier decisions, do not refresh: the next step asks again.

`ml-modeling-autoresearch` runs unattended, so it does not ask. On
`CHANGED`, it records the change in `round-summary.md` and continues. The
next interactive step asks the user.

A hand edit to a step's own output (`modeling/0N-*.md`, `01-data.json`)
needs no hash check. Run again from the next step (see "Hand edits between
steps" in `../ml-system-design/SKILL.md`).

### Closing the loop

- **Upstream.** If a step finds that an upstream decision must change (for
  example, the label horizon does not work, or a source table does not
  exist), tell the user. Offer to update `design/high-level.md` or
  `prd/<topic>.md`. After the update, run `spec_hash_check.sh <project-folder>
  --refresh prd` (or `high-level`).
- **Spec.** After a step records its decision in `0N-*.md`, read the
  Implementation Decisions and Testing Decisions of `spec/<topic>.md`. If
  a line defers this decision to this step ("split rule: to be set by
  `ml-modeling-data`"), or states an assumption that the decision
  contradicts, replace the line with the decision and a pointer to the
  step's file. No hash refresh is necessary.
- **Step decisions** (the features chosen, the model, the split) go in
  that step's own `0N-*.md`. On the hands-on route, these files are the
  deep-dive record.

## Modes

The keyword in the request selects the mode. There are no flags.

| Words in the request | Mode |
|---|---|
| Quick-POC keywords ("Regular and Quick-POC mode" in `../ml-system-design/SKILL.md`) | Quick POC: fewer questions, the first reasonable choice. Same doc quality. |
| "regular", "full", or no mode word | Regular (default): full rigor, ask when a fact is unknown. |

Step 3 has 2 skills for the same `03-train.md`:

| Words in the request | Skill |
|---|---|
| "parallel", "multiagent", "concurrent" | `ml-modeling-multiagent` |
| "sequential", or no preference | `ml-modeling-train` (default) |

Both write `03-train.md` and `model.joblib`, so steps 4 and 5 are the same
on either. Multiagent fits several reasonable candidates or a Quick POC;
train fits one clear candidate, a restricted session, or a low token
budget. Details: "When to use" in `../ml-modeling-multiagent/SKILL.md`.

## Dashboard

Regular and Quick-POC only. Never in monkey-mode.
- `ml-modeling-data` creates `dashboard/eda.ipynb` and `dashboard/app.py`,
  and starts the app.
- The app has 2 sections: EDA (`01-data.json`) and Final Results
  (`04-evaluate.json`). It adds a model comparison if
  `train-candidates/*/metrics.json` exists.
- Features and train write nothing for the dashboard. No later step edits
  `app.py`.

Reason: `../adr/0002-modeling-dashboard.md`.

## Bundled tools

| Script | Requires | Used by |
|---|---|---|
| `scripts/experiment_tracker.py` | python3 stdlib | train, multiagent, evaluate, autoresearch |
| `scripts/feature_selector.py` | python3 stdlib | features |
| `scripts/hypothesis_tester.py` | python3 stdlib | evaluate, critique |
| `scripts/spec_hash_check.sh` | bash, git | each step |
| `../ml-modeling-data/scripts/launch_dashboard.sh` | bash, lsof, curl, uv | data, evaluate |
| `../ml-modeling-serve/scripts/bench_serve.py` | uv (pandas, and what `serve.py` imports) | serve |

The stdlib scripts run with plain `python3`. The step code runs with `uv
run` in the shared sandbox venv. On a new clone, run `uv sync` at the
sandbox root first.

## After step 5

- Iterate: run step 2 or 3 again, then 4 and 5.
- `ml-modeling-autoresearch` (user-run only): automatic improvement
  rounds after step 4. It writes the winners to `04-evaluate.json`; run
  step 5 again after a promotion. Modes: one round,
  `until plateau`, `for 20 minutes`. Not in monkey-mode. Reasons:
  `../adr/0003-autoresearch.md`,
  `../adr/0005-autoresearch-self-contained-looping.md`.
- `ml-critique`: judge the quality of the modeling report (leakage, split,
  baseline, metric).
- To ship: give `modeling/04-evaluate.md` and `modeling/05-serve.md` to
  the `implement` skill.
- A Quick POC that becomes a real project: run `ml-system-design-prd` and
  `ml-system-design-high-level` again in Regular mode, and add `adr/`.

Usage paths: `../adr/0001-ml-modeling-family-and-continuity.md`.
Principles: `../ml-design-principles.md` (Principle 1: start simple; a
more complex model must pass the complexity gate).

## Check

The router's own output is the spec and the step reports. Each step runs
its own Check. When this skill synthesizes `spec/<topic>.md`, do "Check
the output" in `../ml-system-design/SKILL.md`. Intent questions:
1. Does each spec section summarize its source (PRD, ADRs, high-level),
   with no new decisions?
2. Are both hash lines present and equal to `spec_hash_check.sh` output
   (`MATCH`)?
3. Does the Solution name the one model that this folder builds?

Done when the 3 answers are yes and `check_doc.py` prints `OK`.
