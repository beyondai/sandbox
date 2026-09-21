# ML Skills Guide

Orientation for the `ml-system-design-*` / `ml-modeling-*` skill family in
`.agents/skills/personal/`: design an ML system, build and evaluate a model
hands-on, or get a fast autonomous baseline. Everything is chained through
files in a project folder, not conversation memory, so any step can be picked
up in a fresh session by opening the right file.

Operational detail (concurrency, worktrees, autoresearch modes, the skill
improvement log's mechanics) lives in `.agents/skills/personal/README.md`.
Design rationale lives in `.agents/skills/personal/adr/`.

## How it works

Every step has the same shape: **invoke -> it writes a file -> you read it ->
invoke the next step**, which reads what the previous one wrote.

```
/ml-modeling-data
  -> writes modeling/01-data.md and 01-data.json
(you read them)
/ml-modeling-features
  -> reads 01-data, writes modeling/02-features.md
```

## The shape

```
topic
  |
  |--> /ml-system-design-monkey-mode   (optional, runs in the background,
  |      3 questions -> monkey-mode/report.md; touches nothing else)
  v
/ml-system-design-prd          -> prd/<topic>.md
  v
-high-level                    -> design/high-level.md  (fork-grade ML framing)
  v  FORK - pick one
  |--> -deep-dive              -> design/deep-dive.md    (paper)
  |
  '--> ml-modeling-data -> -features -> -train | -multiagent -> -evaluate
                                                -> modeling/01..04  (hands-on)
  v  both routes land here
-delivery                      (cites 04-evaluate.md if modeling ran)
  v
-post-delivery
```

Three things to know:

- **Start with PRD, then high-level.** A new project starts by asking two
  questions: run monkey-mode in parallel? scope with the PRD first? Both are
  hand-run commands.
- **After high-level, choose paper or hands-on.** `-deep-dive` and
  `ml-modeling-*` answer the same four questions (data, features, models,
  training). One writes a design section; the other does the work and records
  it in `modeling/`. `ml-modeling-*` reads `prd/` + `design/high-level.md`,
  never `design/deep-dive.md`.
- **One model per project folder.** If the framing yields two models, the
  second gets its own folder.

## Two speeds

Every skill runs in **Regular** mode (full rigor, asks when unknown) or
**Quick POC** (a one-hour MVP: batched questions, first reasonable choice).
Pick by keyword in the request: "poc", "quick", "mvp", "fast" -> Quick POC;
anything else -> Regular. Monkey-mode is separate: always fast, always
background, never blocks.

## Data

**Practice datasets** are under `data/riot-synthetic/synthetic-data/data/`:
`lifecycle/` (players, per-day activity, purchases, a randomized offer
campaign, a content calendar), `shop/` (items, champion play, purchases,
storefront impressions), `ranked/`, `newplayer/`. The generator is
`data/riot-synthetic/synthetic-data/scripts/riot_practice_data.py`. Each
dataset has a `_truth/` folder with the simulator's latent state - a grading
key, never a modeling input.

**How data enters a project.** `ml-modeling-data` either registers an existing
labeled table or builds one from logs (`modeling/build_dataset.py` ->
`modeling/datasets/<task>_{train,test}.csv`), then records paths, label, id,
and split rule in `01-data.json`'s `dataset` block. Every later step reads
that block: features and train see only the train table, evaluate scores the
test table, and cross-validation folds never cross the split.

## Project folder

Every topic gets one folder, `labs/ml-<topic-slug>-<n>/`:

```
labs/ml-<topic>-<n>/
  prd/<topic>.md           Definition (problem, scope, metrics, team)
  design/high-level.md     ML framing, architecture diagrams, phasing
  design/deep-dive.md      Paper deep dive (only on the paper route)
  adr/000N-*.md            One decision per file
  spec/<topic>.md          Synthesized when modeling starts; pins design hashes
  modeling/
    01-data.md/.json       Profile + `dataset` contract
    02-features.md         Feature decisions
    03-train.md            Model, loss, class weighting
    04-evaluate.md/.json   Metrics vs. baseline; feeds the dashboard
    datasets/, build_dataset.py, experiments.json, autoresearch/
  dashboard/               eda.ipynb + app.py (Streamlit), per-project port
  monkey-mode/report.md    Independent fast baseline
  SKILL-IMPROVEMENTS.md    Proposed fixes to the skills themselves
```

## Command reference

| Skill | Purpose | Command | Plain-language trigger? |
|---|---|---|---|
| `ml-system-design` | Router - whole design doc | `/ml-system-design <topic>` | Yes |
| `ml-system-design-prd` | Grill Definition, write `prd/` | `/ml-system-design-prd <topic>` | No |
| `ml-system-design-definition` | Definition section, no grilling | `/ml-system-design-definition` | Yes |
| `ml-system-design-high-level` | Framing, architecture, phasing; the fork point | `/ml-system-design-high-level` | Yes |
| `ml-system-design-deep-dive` | Paper deep dive (alternative to modeling) | `/ml-system-design-deep-dive` | Yes |
| `ml-system-design-delivery` | Rollout, eval, monitoring, fallback | `/ml-system-design-delivery` | Yes |
| `ml-system-design-post-delivery` | Analysis, explainability, iteration | `/ml-system-design-post-delivery` | Yes |
| `ml-modeling` | Router - data -> features -> train -> evaluate | `/ml-modeling <topic>` | Yes |
| `ml-modeling-data` | Build/register table, profile | `/ml-modeling-data` | Yes |
| `ml-modeling-features` | Engineer features | `/ml-modeling-features` | Yes |
| `ml-modeling-train` | Train one model | `/ml-modeling-train` | Yes |
| `ml-modeling-multiagent` | Train N candidates in parallel | `/ml-modeling-multiagent` | Yes |
| `ml-modeling-evaluate` | Evaluate vs. baseline | `/ml-modeling-evaluate` | Yes |
| `ml-modeling-autoresearch` | Optional auto-improvement loop | `/ml-modeling-autoresearch <project> [mode]` | No |
| `ml-system-design-monkey-mode` | Fast autonomous baseline | `/ml-system-design-monkey-mode <topic>` | No |

## Key design decisions

Each has an ADR in `.agents/skills/personal/adr/`.

- **Files, not memory, between steps** - so any step resumes in a fresh
  session (0001).
- **The fork is after high-level, and it is either/or** - deep-dive on paper
  or ml-modeling hands-on, both feed delivery (0006).
- **A data contract, one model per folder** - `01-data.json`'s `dataset`
  block says where the tables are and how they are split; no step guesses
  from prose (0006, and `ml-modeling-data`).
- **Design drift is detected, then asked about** - the spec pins hashes of
  the PRD and high-level; a changed design doc triggers a question, never a
  silent re-read (0001, 0006).
- **The dashboard is deliberately narrow** - EDA and final results only
  (0002).
- **Autoresearch is self-contained** - one round, until plateau, or for a
  duration, no external scheduler (0003, 0005).
- **Skill fixes are logged, not applied mid-run** - `SKILL-IMPROVEMENTS.md`
  per project, reviewed on request (0004).
