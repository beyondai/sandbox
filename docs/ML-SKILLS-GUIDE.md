# ML Skills Guide

## Contents

- [What the skills do](#what-the-skills-do)
- [How a step works](#how-a-step-works)
- [The flow](#the-flow)
- [Rules to know](#rules-to-know)
- [Two speeds](#two-speeds)
- [Training: one model or several in
  parallel](#training-one-model-or-several-in-parallel)
- [Data](#data)
- [Project folder](#project-folder)
- [Command reference](#command-reference)
  - [Bundled scripts](#bundled-scripts)
  - [Parameters](#parameters)
- [Key design decisions](#key-design-decisions)

## What the skills do

The `ml-system-design-*` and `ml-modeling-*` skills are in
`.agents/skills/personal/`. Use them to do these tasks:
- Design an ML system.
- Build, evaluate, and measure the serving of a model with real data.
- Get a fast baseline that runs in the background.

The steps share files in a project folder, not the conversation. Thus, you
can continue any step in a new session. Open the correct file, and run the
next skill.

Other docs:
- Operation details (concurrency, worktrees, autoresearch modes, the skill
  improvement log): `.agents/skills/personal/README.md`.
- Review of a finished design or modeling report:
  `docs/ML-CRITIQUE-GUIDE.md`.
- The reasons for the design decisions: `.agents/skills/personal/adr/`.
- Style rules for the skill files and the docs, and how to check them:
  `docs/SKILL-STYLE-GUIDE.md`.

The skills are written for Claude Opus 5.5, and tested on it. The evals
are in the `tests/` folder of `ml-system-design`, `ml-modeling`, and
`ml-critique`.

## How a step works

Each step has the same 4 parts:
1. You run the skill.
2. The skill writes a file.
3. You read the file.
4. You run the next skill. It reads the file from the step before it.

```
/ml-modeling-data
  -> writes modeling/01-data.md and 01-data.json
(you read them)
/ml-modeling-features
  -> reads 01-data, writes modeling/02-features.md
```

## The flow

```
/ml-system-design <topic> [poc]   (entry point: selects the mode, offers
  |                                the 2 commands below, runs the sections)
  v
topic
  |
  |--> /ml-system-design-monkey-mode   (optional, background,
  |      3 questions -> monkey-mode/report.md; changes nothing else)
  |--> /ml-system-design-monkey-mlp    (optional, background,
  |      embedding MLP -> monkey-mlp/report.md)
  v
/ml-system-design-prd          -> prd/<topic>.md
  v
-high-level                    -> design/high-level.md  (ML framing)
  v  FORK: select one route
  |--> -deep-dive              -> design/deep-dive.md    (paper)
  |
  '--> ml-modeling-data -> -features -> -train | -multiagent -> -evaluate
         -> -serve                              -> modeling/01..05  (hands-on)
  v  the 2 routes join here
-delivery                      -> design/delivery.md
  v                               (uses 04-evaluate.md and 05-serve.md
  v                                if modeling ran)
-post-delivery                 -> design/post-delivery.md
```

The diagram shows the order. The text below gives the rules.

## Rules to know

1. **Start with `/ml-system-design <topic>`.**
   - It selects Regular or Quick POC from your words.
   - It asks 2 questions: run `/ml-system-design-monkey-mode` in the
     background? Scope with `/ml-system-design-prd` first?
   - You type these 2 commands yourself. Then run `/ml-system-design`
     again. It continues at high-level.
   - The PRD is the Definition section, so `-definition` does not run
     again.
   - `-prd` is the interview. It creates the project folder and writes
     `prd/`. `-definition` is for a project with no PRD, or for a review
     of a Definition.
2. **You can edit each file between steps.**
   - Edit any file in `prd/`, `design/`, `adr/`, `spec/`, or `modeling/`.
     Then tell Claude which file changed.
   - Claude reads the file again, and runs again each later step that uses
     it. It adds a line to the `## Change log` of each changed file.
   - On the hands-on route, a hash check finds edits to `prd/` and
     `design/high-level.md`, also when you do not say.
3. **Docs wrap at 80 columns.** You read the files in a terminal. Prose
   has hard line breaks. Code blocks are not wrapped. A wide table becomes
   a list of headed paragraphs.
4. **After high-level, select paper or hands-on.**
   - `-deep-dive` and `ml-modeling-*` answer the same 5 questions: data,
     features, models, training, serving.
   - `-deep-dive` writes a design section. `ml-modeling-*` does the work
     and records it in `modeling/`.
   - `ml-modeling-*` reads `prd/` and `design/high-level.md`. It never
     reads `design/deep-dive.md`.
5. **One model for each project folder.** If the framing gives 2 models,
   the second model gets its own folder.
6. **`/ml-modeling <topic>` stops after each step.**
   - It runs step 1, reports the result, and waits for you. Then it runs
     step 2, and continues to step 5.
   - To run the 5 steps without stops, say "full chain" or "run all
     steps".
7. **Each skill checks its own output.** The last step of each skill:
   1. **Intent:** answers 2-6 questions for that skill, each yes or no.
   2. **Format:** runs `check_doc.py` on each `.md` file that the skill
      wrote.
   3. **Fix:** fixes the output and checks again, at most 2 times. It
      reports the items that stay open.
   4. **Reflect:** writes each gap in the skill to the shared
      `.agents/skills/personal/SKILL-IMPROVEMENTS.md`.

   At the end of every session that used an ml-* skill, the agent also
   reflects on the whole session and offers to review the proposed
   entries (sandbox `CLAUDE.md`).

   The skills with many steps also show a progress checklist. They tick
   each line.

## Two speeds

Each skill has 2 modes:
- **Regular:** full rigor. The skill asks when a fact is unknown.
- **Quick POC:** a one-hour MVP at the same quality. The skill asks fewer
  questions and takes the first reasonable choice.

A keyword in your request selects the mode:
- "poc", "quick", "mvp", "prototype", "fast", "one hour", "1 hour" select
  Quick POC.
- All other words select Regular.

In the modeling chain, the first step writes the mode into the spec. A
later step with no mode word keeps that mode; a mode word overrides it
for that step.

Monkey-mode is different. It is always fast and always runs in the
background. It waits for you only on one question: which data to use.

## Training: one model or several in parallel

Step 3 (train) has 2 skills. Both write `03-train.md` and `model.joblib`,
so evaluate (step 4) and serve (step 5) are the same after either one.

```
                     ┌─ subagent: logistic regression ─┐
02-features.md ────> ├─ subagent: GBDT                 ├─> compare -> winner
(train table)        └─ subagent: two-tower / MLP     ─┘    03-train.md
                       each: CV, metrics, 1-row p99         model.joblib
```

- **`mm-train`** (the default) trains 1 model, and the simplest option
  for comparison, in sequence.
- **`mm-multiagent`** trains several candidates at the same time, with 1
  subagent for each candidate. Then it keeps 1 winner.

**Use multiagent when:**
- several candidates are reasonable (the Phasing names more than 1 model
  class, or you do not know if GBDT beats a linear model);
- speed matters (Quick POC): the total time is close to the time of 1
  candidate;
- you want evidence for the choice: a table with the metric and its
  noise, training time, inference time, and explainability.

**Use train when:**
- 1 candidate is the clear choice;
- the session cannot give subagents write access;
- you want to use fewer tokens (the cost grows with each candidate).

If you do not choose and the Phasing names 2 or more model classes, the
skill suggests multiagent in one line.

**How to start it:**
- `/ml-modeling <topic> parallel` ("multiagent" or "concurrent" also
  work). Add "poc" for 3-fold CV and about half the trees.
- Or `/ml-modeling-multiagent` alone, when steps 1 and 2 are done.

**Before you start:** use auto mode. Subagents get the permissions of
the session. In plan mode they write a plan, stop, and report success.
The skill checks the mode and makes 1 test write. If either fails, it
tells you and waits.

**How it selects the winner:**
1. The simplest candidate inside the noise of the best one wins.
2. A more complex candidate wins only if it passes the complexity gate.
3. A candidate over the PRD p99 latency does not win unless you accept
   it.
4. A close result: the skill shows the table, and you select.

The winner is refit on the full train table. Its threshold comes from
out-of-fold predictions. The other candidates stay in
`train-candidates/<type>/`.

**A risk to know: the CV leak.** A feature built from the target over the
whole table (leave-one-out or target encoding) leaks into CV. Boosted
models use the leak most, so the wrong candidate can win. The skill
computes the feature again in each fold, or marks the ranking as
provisional.

## Data

**Practice datasets** are in `data/riot-synthetic/synthetic-data/data/`:
- `lifecycle/`: players, activity for each day, purchases, a randomized
  offer campaign, a content calendar.
- `shop/`: items, champion play, purchases, storefront impressions.
- `ranked/` and `newplayer/`.

The generator is
`data/riot-synthetic/synthetic-data/scripts/riot_practice_data.py`. Each
dataset has a `_truth/` folder with the hidden state of the simulator. Use
it only to grade results. Never use it as a model input.

**How data enters a project:**
1. `ml-modeling-data` registers an existing labeled table, or builds one
   from logs: `modeling/build_dataset.py` writes
   `modeling/datasets/<task>_{train,test}.csv`, or parquet under
   `data/<dataset>/modeling/` for tables over about 1M rows.
2. It records the paths, the label, the id, and the split rule in the
   `dataset` block of `01-data.json`. For implicit labels (only positives
   in the logs), it also builds and records the negatives.
3. Each later step reads that block. Features and train use only the
   train table. Evaluate scores the test table. Cross-validation folds
   never cross the split.
4. The data step also cleans real errors (impossible values, a code for
   "missing", exact duplicates), and then profiles again. An extreme but
   real value keeps its flag, and stays unchanged (ADR 0007).

## Project folder

Each project has one folder: `<parent>/<project>/`.
- The project name is the name that you give, for example `proj1`.
- The parent is `labs/`, unless you name another parent.
- Full rule: `ml-system-design/SKILL.md`, "Project folder" (ADR 0010).

```
labs/proj1/
  prd/<topic>.md           Definition (problem, scope, baseline, metrics, team)
  design/high-level.md     ML framing, architecture diagrams, phasing
  design/deep-dive.md      Paper deep dive (paper route only)
  design/delivery.md       Rollout, evaluation, monitoring, fallback
  design/post-delivery.md  Analysis, explainability, iteration, democratize
  adr/000N-*.md            One decision in each file
  spec/<topic>.md          Made when modeling starts; holds the design hashes
  modeling/
    01-data.md/.json       Profile, cleaning, and the `dataset` contract
    02-features.md         Feature decisions; features.py
    03-train.md            Model, loss, training setup; model.joblib
    04-evaluate.md/.json   Metrics against the baseline; test_scores.csv
    05-serve.md/.json      Mode, latency, capacity, cost; serve.py
    datasets/, build_dataset.py, experiments.json, autoresearch/
  dashboard/               eda.ipynb + app.py (Streamlit), own port
  monkey-mode/report.md    Independent fast baseline
  critique/<date>-<lens>.md  Critiques from ml-critique
  critique/<date>-final.md   Final critique from ml-critique-merge
  critique/<date>-share-out.md  Share-out plan from ml-critique-share-out
  research/                Research notes for this project
  SKILL-IMPROVEMENTS.md    Older skill proposals (history; new ones go
                           to the shared log in .agents/skills/personal/)
```

## Command reference

`sd-*` is short for `ml-system-design-*`. `mm-*` is short for
`ml-modeling-*`. You run each skill as `/<full name>`, for example
`/ml-modeling-data`. A skill marked `cmd` runs only by command. The other
skills also start from plain language.

| Skill                 | What it does                                   |
|-----------------------|------------------------------------------------|
| `sd`                  | Router for the full design doc                 |
| `sd-prd` cmd          | Interview on the Definition, writes `prd/`     |
| `sd-definition`       | Definition section, no interview               |
| `sd-high-level`       | Framing, architecture, phasing; the fork       |
| `sd-deep-dive`        | Paper deep dive, serving included (or `mm-*`)  |
| `sd-delivery`         | Rollout, evaluation, monitoring, fallback      |
| `sd-post-delivery`    | Analysis, explainability, iteration, reuse     |
| `sd-monkey-mode` cmd  | Fast baseline in the background                |
| `sd-monkey-mlp` cmd   | Fast embedding-MLP baseline, background        |
| `mm`                  | Router: data, features, train, evaluate, serve |
| `mm-data`             | Builds the table, profiles and cleans it       |
| `mm-features`         | Makes the features                             |
| `mm-train`            | Trains one model                               |
| `mm-multiagent`       | Trains N candidates in parallel                |
| `mm-evaluate`         | Evaluates against a baseline                   |
| `mm-serve`            | Measures latency; sizes capacity and cost      |
| `mm-autoresearch` cmd | Optional automatic improvement loop            |
| `ml-critique`         | Critiques a finished write-up (critique guide) |
| `ml-critique-merge`   | Merges critiques into one final critique       |
| `ml-critique-share-out` | Plans what to discuss in a fixed time        |

### Bundled scripts

The paths start at `.agents/skills/personal/`. Run the scripts from the
sandbox root.

- `ml-system-design/scripts/check_doc.py <files or dirs>`
  - Checks the output format: 80 columns, wide tables, em dashes, code
    fences, required sections (`--sections`).
  - Prints `OK` or `file:line: reason`.
  - Needs: Python stdlib.
- `ml-modeling/scripts/spec_hash_check.sh <project>`
  - Finds a change to the PRD or high-level since the spec.
  - Prints `MATCH`, or `CHANGED` with both SHAs. `--refresh prd` or
    `--refresh high-level` updates the hash.
  - Needs: Bash, git.
- `ml-modeling-data/scripts/launch_dashboard.sh <project>`
  - Starts the project dashboard on a free port, or uses the one that
    runs. Prints the URL. `--stop` stops it.
  - It stops or uses only its own process.
  - Needs: Bash, lsof, curl, uv.
- `ml-modeling/scripts/experiment_tracker.py`: the experiment log. "Best"
  is the lowest value for error and loss metrics. Python stdlib.
- `ml-modeling/scripts/feature_selector.py`: a rough feature ranking.
  Python stdlib for CSV. For parquet, run it with `uv run` and add
  `--sample N --drop <id columns>`.
- `ml-modeling/scripts/hypothesis_tester.py`: significance tests for
  means and proportions. Python stdlib.
- `ml-modeling-serve/scripts/bench_serve.py --serve <serve.py> --rows <csv>`
  - Times the project's `score(df)`: p50/p99 for 1 row, batch rows per
    second, model size. Prints JSON.
  - `--full` (and `--chunk N`) times a whole batch job in file order: use
    it for batch serving.
  - Needs: uv (pandas, and what `serve.py` imports).
- `scripts/check_skill_style.py .agents/skills/personal`
  - Checks the skill files against `docs/SKILL-STYLE-GUIDE.md`.
  - Prints `OK` or `file:line: reason`.
  - Needs: Python stdlib.
- `scripts/check_docs.py`
  - Checks `docs/` for style, and for consistency with the skills: each
    skill named, each cited ADR present, links and paths that resolve.
  - Prints `OK` or `file:line: reason`.
  - Needs: Python stdlib.

On a new clone, run `uv sync` at the sandbox root first.

### Parameters

Type free text after the command. There are no flags. The skills know 4
types of words:
- **Topic or project.** `churn prediction` starts a new folder.
  `labs/ml-riot-churn-2` continues an existing folder.
- **Speed.** The Quick-POC keywords (see "Two speeds"). All other words
  select Regular.
- **Training.** `parallel` or `multiagent` selects `mm-multiagent`. All
  other words select `mm-train`. This applies only through `/mm`.
- **Continuation** (only for `/mm`). `full chain` or `run all steps`
  runs data -> features -> train -> evaluate -> serve without stops. All other
  words make the skill stop and wait after each step.

| Command                          | Takes                                   |
|----------------------------------|-----------------------------------------|
| `/sd <topic>`                    | topic, speed                            |
| `/sd-prd <topic>`                | topic (required), speed                 |
| `/sd-definition`..`-post-delivery` | project*, speed, `review`             |
| `/sd-monkey-mode <topic>`        | topic (required)                        |
| `/sd-monkey-mlp <topic>`         | topic (required)                        |
| `/mm <topic>`                    | topic or project, speed, training, cont. |
| `/mm-data` .. `/mm-serve`        | project*, speed                         |
| `/mm-autoresearch <project> ...` | project (required), stop, count         |

Notes:
- "cont." is continuation.
- \* Give the project only when the conversation does not make it clear.
- `review` reviews the section. It does not write a draft.
- Autoresearch stop rule: `until plateau`, `for N minutes`, or no words
  (one round). Count: `N candidates`.

## Key design decisions

Each decision has an ADR in `.agents/skills/personal/adr/`. The number is
in parentheses.

- **Files, not memory, connect the steps.** Thus, any step can continue
  in a new session (0001).
- **The fork is after high-level, and you select one route.** The paper
  deep dive or the hands-on ml-modeling chain. Both go to delivery
  (0006).
- **A data contract, and one model for each folder.** The `dataset` block
  in `01-data.json` gives the table paths and the split. No step guesses
  from prose (0006, and `ml-modeling-data`).
- **The skills find design changes, then ask.** The spec holds hashes of
  the PRD and high-level. A changed design doc starts a question. The
  skill never reads the change silently (0001, 0006).
- **The dashboard is small on purpose.** It shows the EDA and the final
  results only (0002).
- **Autoresearch controls its own loop.** One round, until plateau, or for
  a time. No external scheduler (0003, 0005).
- **Ranking is a first-class task.** Train folds by query and scores per
  query; evaluate scores against the full truth, per query and item
  segment. With proxy data, each finding gets a "For <target>" line
  (0017).
- **Skill changes go to one shared log.**
  `.agents/skills/personal/SKILL-IMPROVEMENTS.md`, for all projects. The
  agent reflects at the end of each session and offers a review. An
  agent-found entry needs evidence that the skill made the work worse
  (0004, 0016, 0019).
- **One reference for model and training choices.** `ml-model-training.md`
  holds negative sampling, architecture (shallow or deep, MLP, cross
  network, attention), the neural network training setup, and tree
  hyperparameters. Deep-dive, train, and the critique lenses check that a
  write-up states them (0012).
- **Serving on both routes.** Deep-dive has a Serving item. The hands-on
  chain has step 5, `mm-serve`, which measures latency and sizes the
  capacity for the peak load. Delivery gets the same facts on both
  routes, and its load test uses them (0013).
- **Style rules are written and checked.** `docs/SKILL-STYLE-GUIDE.md`,
  `check_skill_style.py`, and `check_docs.py`. The docs are updated and
  checked after each skill change. The skills are checked after each
  major skill change (0014).
- **Each skill family has evals.** At least 3 tests for each family, run
  on Opus only. Scripts have no unexplained numbers (0015).
- **Simple by default, complex only with evidence.** The complexity gate
  in `ml-design-principles.md` applies to design, training, and critique.
- **Critique is different from Review mode.** It is a review by a reader
  with no context, with priorities, convergence, and a record of the
  decisions (0009).
- **Critique covers every design step, most important first.** A
  coverage map links each design and modeling skill item to a catalog
  check. Each run asks for the view (fresh or with your design) and a
  critique context; the context wins only on a conflict, and each
  conflict is noted (0018). Each question gives why it matters and what
  each answer changes (0019).
- **One critique mode; the share-out cuts for time.** Each run checks
  the full catalog, because the agent part takes minutes.
  `ml-critique-merge` joins critiques into a final critique.
  `ml-critique-share-out` plans what to discuss in a fixed time. New
  user findings get `[user]`. Done well lists only strengths that are
  costly to lose (0020).
- **A share-out never cuts a P1.** A required topic gets a point only
  if the P1 points leave time; the user is told if not (0021).
- **One folder for each project.** All generated files go in
  `<parent>/<project>/`, never in `notes/` (0010).
- **Each skill checks its own output.** Intent questions, a format script,
  a fix loop, and a log of skill issues. Scripts do the fragile steps
  (0011).
- **Cleaning is part of the data step.** The data step fixes real errors
  and profiles again. Feature engineering does not do it, and it is not a
  separate step (0007).
