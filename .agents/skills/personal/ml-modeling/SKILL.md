---
name: ml-modeling
description: Use when executing the hands-on ML modeling workflow for a project that already has (or is about to get) an ml-system-design-deep-dive decision — profiling data, engineering features, training a model, and evaluating it. Entry point for the whole data-to-evaluated-model chain; for one step only, trigger that step's own skill directly instead. Trigger on "let's build/train/prototype a model for X," "quick ML POC," or continuing modeling work in an existing ml-<topic>-<n>/ project folder.
---

# ML Modeling

Four sequential steps, each its own skill, chained by files under `ml-<topic>-<n>/modeling/` — not conversation memory, so any step can be invoked standalone in a fresh session:

1. `ml-modeling-data` — profile data → `modeling/01-data.md`
2. `ml-modeling-features` — engineer features → `modeling/02-features.md`
3. `ml-modeling-train` (sequential) **or** `ml-modeling-multiagent` (parallel, see below) — train → `modeling/03-train.md`
4. `ml-modeling-evaluate` — evaluate → `modeling/04-evaluate.md`

For the full chain, invoke each in order. For a single-step ask ("engineer features for this dataset"), invoke that skill directly — it reads whatever the previous step already wrote and continues from there.

## Required upstream dependency: `design/deep-dive.md`

Every step here reads `<project-folder>/design/deep-dive.md`, written by `ml-system-design-deep-dive` — this is true in both Regular and Quick-POC mode. If it doesn't exist yet, don't invent a substitute: run `ml-system-design-deep-dive` first (POC mode if speed matters — see below), then come back. This is the one hard dependency that makes `ml-modeling-*` reliable — it grounds every step in real decisions instead of assumptions made up mid-chain.

**`spec/<topic>.md`**: the first time any `ml-modeling-*` step runs against a project that has `design/deep-dive.md` but no `spec/<topic>.md` yet, synthesize one — `prd/` + `adr/` + `design/deep-dive.md` distilled into an implementation-ready doc: Problem Statement, Solution, Implementation Decisions, Testing Decisions, Out of Scope. This is the fork point between designing and executing; full rationale in `../adr/0001-ml-modeling-family-and-continuity.md`.

## Regular vs. Quick-POC mode

- **Regular**: full rigor at every step, ask when unknown.
- **Quick POC**: a one-hour MVP, not lower documentation quality — favor speed once past the required `design/deep-dive.md` (itself produced fast via that skill's own POC mode): fewer clarifying questions, first-reasonable-choice over exhaustive comparison.

Mode is chosen by keyword, not a flag, since this skill family has no structured argument syntax:

| Words in the request | Mode |
|---|---|
| "poc", "quick", "mvp", "prototype", "fast", "one hour"/"1 hour" | Quick POC |
| "regular", "full", or no mode word | Regular (default) |

## Sequential vs. parallel training

Step 3 has two producers for the same `modeling/03-train.md` slot — pick one per run, same keyword mechanism:

| Words in the request | Skill |
|---|---|
| "parallel", "multiagent", "concurrent" | `ml-modeling-multiagent` |
| "sequential", or no preference stated | `ml-modeling-train` (default) |

`ml-modeling-multiagent` trains every candidate model type `design/deep-dive.md` named (or the algorithm-selection matrix's short-list, if none was specified) concurrently, each in its own `modeling/train-candidates/<model-type>/`, then compares and writes the winner to `03-train.md`. Full rationale for why this is safe without git worktrees (unlike mattpocock's `implement-spec`, which this pattern is adapted from) is in the ADR.

## Dashboard — deliberately narrow, Regular/Quick-POC only

`ml-modeling-data` creates `dashboard/eda.ipynb` (real executed EDA) and bootstraps `dashboard/app.py` (Streamlit), launched as a background process. Only two sections: EDA (from `01-data.json`) and Final Results (from `04-evaluate.json`, written by `ml-modeling-evaluate`), plus an optional model-comparison section that reads `train-candidates/*/metrics.json` if `ml-modeling-multiagent` ran. `ml-modeling-features` and `ml-modeling-train`/`-multiagent` write nothing for the dashboard and are untouched by it — feature-engineering and training detail stay in their `.md` files, not duplicated onto a chart. `app.py` itself is written once and never edited by a later step; it just reads whatever JSON exists. Full rationale (why this scope and not a full per-step mirror) in `../adr/0002-modeling-dashboard.md`.

Never runs in monkey-mode — that family shares only the project-folder root and stays fully separate (see `ml-system-design-monkey-mode`).

## Bundled tools

`scripts/experiment_tracker.py`, `scripts/feature_selector.py`, `scripts/hypothesis_tester.py` — stdlib-only, run with plain `python3`, no project venv needed. Referenced from the relevant step skills; shared here since `experiment_tracker.py` spans both train and evaluate.

## Closing the loop

If executing a step reveals something that should change an earlier decision (e.g. feature engineering surfaces a feature `design/deep-dive.md` didn't list), flag it and offer to update `design/deep-dive.md` — don't silently drift from the recorded decisions.

## Skill improvement log

Any `ml-modeling-*` skill, while it runs, may turn up something about the *skill itself* worth fixing — not the project it's working on. Two triggers:

1. **Agent-found**: a bug in this skill's own instructions, or a genuinely better way to do the step than what's written.
2. **User-requested**: you ask to change how the skill behaves — as opposed to a one-off request specific to this project's data or model.

Log it to `<project-folder>/SKILL-IMPROVEMENTS.md` (created on first entry, appended to after) rather than editing the actual `SKILL.md` on the spot — keeps the skill files stable mid-run and gives you a batch to review later instead of drive-by edits:

```markdown
## <date> — <skill-name>
- **Source**: agent-found bug | agent-found better design | user-requested
- **Status**: proposed
- **Finding**: <what's wrong or what could be better, concretely>
- **Suggested change**: <the actual edit, concrete enough to apply as-is>
```

**Review**: any skill in the family, at the end of a run (after doing the task actually asked for, never blocking it), checks this file for entries still marked `proposed`. If any exist, say so and offer to review them now. Per entry: ask adopt or decline; an adopted entry gets applied as a real edit to the corresponding skill file under `.agents/skills/personal/<skill>/SKILL.md`, then the entry's `Status` flips to `adopted` or `declined`. Never delete an entry — `SKILL-IMPROVEMENTS.md` stays a durable per-project record of what was proposed and decided. Same convention on the `ml-system-design-*` side; full rationale in `../adr/0004-skill-improvement-log.md`.

## Where this leads

After step 4, either iterate (rerun step 2 or 3), hand `modeling/04-evaluate.md` to mattpocock's `implement` skill by hand to productionize, or — if this graduated from a Path A quick POC into a real project — backfill `prd/` and a full `adr/` via `ml-system-design-prd` / `ml-system-design-high-level`. Full usage-path tables (both the modeling-focused path and the whole-design path that forks into this one) are in `../adr/0001-ml-modeling-family-and-continuity.md`.
