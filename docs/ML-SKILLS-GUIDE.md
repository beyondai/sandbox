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
/ml-system-design <topic> [poc]   (entry point: picks the mode, offers the
  |                                two commands below, then runs the sections)
  v
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

- **Start with `/ml-system-design <topic>`.** It picks Regular vs. Quick POC
  from your wording, then asks two questions: run
  `/ml-system-design-monkey-mode` in parallel? scope with
  `/ml-system-design-prd` first? Both are hand-run commands; answer them, then
  come back to `/ml-system-design` and it continues at high-level - the PRD
  is the Definition section, so `-definition` is not run again. (`-prd` is the
  interview: hand-run, creates the folder, writes `prd/`. `-definition` is the
  checklist and the drafted section for a project without a PRD.)
- **Every file is yours to edit between steps.** Open any `prd/`, `design/`,
  `adr/`, `spec/` or `modeling/` file, change it, and tell Claude which one;
  it re-reads it and re-runs the downstream steps that cite it, noting the
  change in that file's `## Change log`. On the hands-on route the hash
  check in the spec catches edits to `prd/` and `design/high-level.md` even
  if you forget to say.
- **Docs wrap at 80 columns.** Every file the skills write is meant to be
  read in a terminal: prose hard-wrapped, code blocks exempt, wide tables
  turned into headed paragraphs.
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

`sd-*` is short for `ml-system-design-*`, `mm-*` for `ml-modeling-*`. Every
skill runs as `/<full name>` (e.g. `/ml-modeling-data`); those marked `cmd`
run only by command, the rest also trigger from plain language.

| Skill                 | What it does                                  |
|-----------------------|-----------------------------------------------|
| `sd`                  | Router for the whole design doc               |
| `sd-prd` cmd          | Grill the Definition, write `prd/`            |
| `sd-definition`       | Definition section, no grilling               |
| `sd-high-level`       | Framing, architecture, phasing; the fork      |
| `sd-deep-dive`        | Paper deep dive (alternative to `mm-*`)       |
| `sd-delivery`         | Rollout, eval, monitoring, fallback           |
| `sd-post-delivery`    | Analysis, explainability, iteration           |
| `sd-monkey-mode` cmd  | Fast autonomous baseline, background          |
| `mm`                  | Router: data -> features -> train -> evaluate |
| `mm-data`             | Build or register the table, profile it       |
| `mm-features`         | Engineer features                             |
| `mm-train`            | Train one model                               |
| `mm-multiagent`       | Train N candidates in parallel                |
| `mm-evaluate`         | Evaluate against a baseline                   |
| `mm-autoresearch` cmd | Optional auto-improvement loop                |

### Parameters

Free text after the command, no flags. Three kinds of words are recognized:

- **topic or project** - `churn prediction` starts a new folder;
  `labs/ml-riot-churn-2` continues an existing one.
- **speed** - `poc`, `quick`, `mvp`, `fast`, `one hour` -> Quick POC;
  anything else -> Regular.
- **training** - `parallel` or `multiagent` -> `mm-multiagent`; otherwise
  `mm-train`. Only matters when going through `/mm`.

| Command                              | Takes                             |
|--------------------------------------|-----------------------------------|
| `/sd <topic>`                        | topic, speed                      |
| `/sd-prd <topic>`                    | topic (required), speed           |
| `/sd-definition` .. `-post-delivery` | project*, speed, `review`         |
| `/sd-monkey-mode <topic>`            | topic (required)                  |
| `/mm <topic>`                        | topic or project, speed, training |
| `/mm-data` .. `/mm-evaluate`         | project*, speed                   |
| `/mm-autoresearch <project> ...`     | project (required), stop, count   |

\* only when the project is not clear from the conversation. `review` runs
the section in review mode instead of drafting. Autoresearch stop rule:
`until plateau`, `for N minutes`, or nothing (one round); count: `N
candidates`.

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
