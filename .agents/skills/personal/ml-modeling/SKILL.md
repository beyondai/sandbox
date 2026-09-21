---
name: ml-modeling
description: >-
  Use when executing the hands-on ML modeling workflow for a project that
  already has a PRD and a fork-grade `design/high-level.md` — building the
  labeled table, profiling data, engineering features, training a model, and
  evaluating it. The hands-on alternative to ml-system-design-deep-dive.
  Entry point for the whole data-to-evaluated-model chain; for one step only,
  trigger that step's own skill directly instead. Trigger on "let's
  build/train/prototype a model for X," "quick ML POC," or continuing modeling
  work in an existing ml-<topic>-<n>/ project folder.
---

# ML Modeling

Four sequential steps, each its own skill, chained by files under
`ml-<topic>-<n>/modeling/` — not conversation memory, so any step can be invoked
standalone in a fresh session:

1. `ml-modeling-data` — build or register the labeled table, record it in
   `01-data.json`'s `dataset` block, profile → `modeling/01-data.md`
2. `ml-modeling-features` — engineer features → `modeling/02-features.md`
3. `ml-modeling-train` (sequential) **or** `ml-modeling-multiagent` (parallel,
   see below) — train → `modeling/03-train.md`
4. `ml-modeling-evaluate` — evaluate → `modeling/04-evaluate.md`

`dataset` is the data contract: later steps read table paths, label, and
split roles from it, never from prose. One model per project folder.

For the full chain, invoke each in order. For a single-step ask ("engineer
features for this dataset"), invoke that skill directly — it reads whatever the
previous step already wrote and continues from there.

## Which project folder

Use, in order: the folder named in the request; else the `labs/ml-*` folder
whose files this conversation has already been reading or writing; else, if
exactly one `labs/ml-*` folder exists, that one; otherwise ask. Section and
step skills never create a folder - that is `/ml-system-design-prd`'s job.

## Output docs

Every `.md` this family writes follows `../ml-system-design/SKILL.md`,
"Output docs": prose wrapped at 80 columns, code blocks exempt, wide tables
turned into headed paragraphs.

## Required upstream: PRD + fork-grade high-level design

Every step here reads `<project-folder>/prd/<topic>.md` and
`<project-folder>/design/high-level.md`, in both Regular and Quick-POC mode.
If either is missing, don't invent a substitute: run `/ml-system-design-prd`
and `/ml-system-design-high-level` first (POC mode if speed matters), then
come back. High-level's ML framing must be fork-grade — per model: prediction
target, label definition and horizon, scoring population and cadence, unit of
prediction, known exclusions — and its Architecture diagram must name the
concrete source tables. That framing is what grounds every step below.

**Where the fork sits.** After high-level, a project takes one of two routes
to the same place:

```
prd -> high-level -> [ ml-system-design-deep-dive (paper) | ml-modeling-* (hands-on) ] -> delivery
```

`ml-modeling-*` is the hands-on, more detailed version of the deep dive: the
same questions (data, features, models, training) answered by doing the work
and recording it in `modeling/01`-`04`. It does not read
`design/deep-dive.md`. If a project has both, whichever was written last is
the record `ml-system-design-delivery` cites. Rationale in
`../adr/0006-fork-after-high-level.md`.

**Where each step gets its grounding** (replaces reading deep-dive sections):

| Step | Reads | Decides and records itself |
|---|---|---|
| `ml-modeling-data` | framing (target, label, horizon, population, exclusions); Architecture's source tables; PRD scope | the train/test split and cutoffs -> `dataset` block in `01-data.json`, reasoning in `01-data.md` |
| `ml-modeling-features` | framing (population, unit); `01-data.md` | the feature list -> `02-features.md` |
| `ml-modeling-train` / `-multiagent` | Phasing (model class per phase); algorithm-selection matrix; `01-data` class balance | candidates, loss, class weighting -> `03-train.md` |
| `ml-modeling-evaluate` | PRD Metrics — offline (primary, secondary, guardrails); `dataset.split` | -> `04-evaluate.md` / `.json` |

**`spec/<topic>.md`**: the first time any `ml-modeling-*` step runs against a
project that has both upstream files but no `spec/<topic>.md` yet, synthesize
one — `prd/` + `adr/` + `design/high-level.md` distilled into an
implementation-ready doc: Problem Statement, Solution, Implementation Decisions,
Testing Decisions, Out of Scope. Its first two lines are `prd-hash: <sha>` and
`high-level-hash: <sha>`, each from `git hash-object -w <file>` (the `-w` stores
the blob so it stays diffable even if that version was never committed). Full
rationale in `../adr/0001-ml-modeling-family-and-continuity.md` and
`../adr/0006-fork-after-high-level.md`.

Spec template - each section is a distillation, not a copy:

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

## Regular vs. Quick-POC mode

- **Regular**: full rigor at every step, ask when unknown.
- **Quick POC**: a one-hour MVP, not lower documentation quality — favor speed
  once past the required PRD and high-level (both have their own POC modes):
  fewer clarifying questions, first-reasonable-choice over exhaustive
  comparison.

Mode is chosen by keyword, not a flag, since this skill family has no structured
argument syntax:

| Words in the request | Mode |
|---|---|
| "poc", "quick", "mvp", "prototype", "fast", "one hour"/"1 hour" | Quick POC |
| "regular", "full", or no mode word | Regular (default) |

## Sequential vs. parallel training

Step 3 has two producers for the same `modeling/03-train.md` slot — pick one per
run, same keyword mechanism:

| Words in the request | Skill |
|---|---|
| "parallel", "multiagent", "concurrent" | `ml-modeling-multiagent` |
| "sequential", or no preference stated | `ml-modeling-train` (default) |

`ml-modeling-multiagent` trains every candidate model type high-level's Phasing
names (plus the algorithm-selection matrix's short-list, if Phasing names only
one) concurrently, each in its own `modeling/train-candidates/<model-type>/`,
then compares and writes the winner to `03-train.md`. Full rationale for why
this is safe without git worktrees (unlike mattpocock's `implement-spec`, which
this pattern is adapted from) is in the ADR.

## Dashboard — deliberately narrow, Regular/Quick-POC only

`ml-modeling-data` creates `dashboard/eda.ipynb` (real executed EDA) and
bootstraps `dashboard/app.py` (Streamlit), launched as a background process.
Only two sections: EDA (from `01-data.json`) and Final Results (from
`04-evaluate.json`, written by `ml-modeling-evaluate`), plus an optional
model-comparison section that reads `train-candidates/*/metrics.json` if
`ml-modeling-multiagent` ran. `ml-modeling-features` and
`ml-modeling-train`/`-multiagent` write nothing for the dashboard and are
untouched by it — feature-engineering and training detail stay in their `.md`
files, not duplicated onto a chart. `app.py` itself is written once and never
edited by a later step; it just reads whatever JSON exists. Full rationale (why
this scope and not a full per-step mirror) in
`../adr/0002-modeling-dashboard.md`.

Never runs in monkey-mode — that family shares only the project-folder root and
stays fully separate (see `ml-system-design-monkey-mode`).

## Optional follow-up: `ml-modeling-autoresearch`

Once `modeling/04-evaluate.json` exists, `ml-modeling-autoresearch`
(user-invoked only) becomes available — not a step in the chain above, an opt-in
extra. A round: a couple of parallel candidates each try one change, the winner
is kept if it beats the current best, promoted results flow straight into
`04-evaluate.json` (the dashboard picks it up with zero code changes). Three
modes, self-contained — no external scheduling: `/ml-modeling-autoresearch
<project>` (one round), `... until plateau` (keeps going until a non-improvement
streak or the round ceiling), `... for 20 minutes` (also bounded by a duration,
stopping early on plateau). Works in Regular and Quick-POC mode; never in
monkey-mode. Full usage and design rationale in
`ml-modeling-autoresearch/SKILL.md`, `../adr/0003-autoresearch.md`, and
`../adr/0005-autoresearch-self-contained-looping.md`.

## Bundled tools

`scripts/experiment_tracker.py`, `scripts/feature_selector.py`,
`scripts/hypothesis_tester.py` — stdlib-only, run with plain `python3`, no
project venv needed. Referenced from the relevant step skills; shared here since
`experiment_tracker.py` spans both train and evaluate.

## Closing the loop

If executing a step reveals something that should change an upstream decision
— the framing, a source table, the phasing (e.g. the label horizon turns out
unworkable, or a named source doesn't exist) — flag it and offer to update
`design/high-level.md` or `prd/<topic>.md`; don't silently drift from the
recorded decisions. After such an update, rewrite that file's hash line in
the spec with the new `git hash-object -w <file>` so the check below doesn't
re-ask about a change this chain made itself. Decisions that belong to the
step itself (features chosen, model picked, split used) are recorded in that
step's own `.md` — that is the hands-on deep dive's record.

### Design docs changed?

The design session can keep editing `prd/<topic>.md` or
`design/high-level.md` while modeling runs. Every step skill runs this check
first, before its own work, in both Regular and Quick-POC mode:

1. `git hash-object <file>` vs. the spec's `prd-hash:` and `high-level-hash:`
   lines. Both equal: proceed, say nothing.
2. Different: show what changed — `git diff <recorded-hash> -- <file>`,
   summarized to which sections moved and how — then ask two questions before
   doing the step:
   - Re-synthesize `spec/<topic>.md` from the current design docs now, or
     keep the current spec?
   - Apply the changed decisions in this step and later ones, or proceed on the
     previous decisions?
3. Record the answer as one line in the step's output `.md` (e.g. `high-level
   changed since spec (ML framing); user chose: apply going forward, spec
   kept`) so a later session sees the choice. If the spec was re-synthesized, or
   the user chose to apply the change going forward, refresh that hash line
   with `git hash-object -w` so the same change isn't asked about again. If the
   user chose to proceed on the previous decisions, leave the hash alone — the
   next step asks again, which is intended: each step is a fresh chance to pick
   the change up.

`ml-modeling-autoresearch` is autonomous and does not ask; on a mismatch it
notes the change in `round-summary.md` and keeps running against the current
file. The next interactive step surfaces the question.

Hand edits to a step's own output (`modeling/0N-*.md`, `01-data.json`) need
no hash check: the next step reads the file as it stands. When the user says
one changed, re-run from the step after it; see `../ml-system-design/SKILL.md`,
"Hand edits between steps".

## Skill improvement log

Any `ml-modeling-*` skill, while it runs, may turn up something about the *skill
itself* worth fixing — not the project it's working on. Two triggers:

1. **Agent-found**: a bug in this skill's own instructions, or a genuinely
   better way to do the step than what's written.
2. **User-requested**: you ask to change how the skill behaves — as opposed to a
   one-off request specific to this project's data or model.

Log it to `<project-folder>/SKILL-IMPROVEMENTS.md` (created on first entry,
appended to after) rather than editing the actual `SKILL.md` on the spot — keeps
the skill files stable mid-run and gives you a batch to review later instead of
drive-by edits:

```markdown
## <date> — <skill-name>
- **Source**: agent-found bug | agent-found better design | user-requested
- **Status**: proposed
- **Finding**: <what's wrong or what could be better, concretely>
- **Suggested change**: <the actual edit, concrete enough to apply as-is>
```

**Review**: any skill in the family, at the end of a run (after doing the task
actually asked for, never blocking it), checks this file for entries still
marked `proposed`. If any exist, say so and offer to review them now. Per entry:
ask adopt or decline; an adopted entry gets applied as a real edit to the
corresponding skill file under `.agents/skills/personal/<skill>/SKILL.md`, then
the entry's `Status` flips to `adopted` or `declined`. Never delete an entry —
`SKILL-IMPROVEMENTS.md` stays a durable per-project record of what was proposed
and decided. Same convention on the `ml-system-design-*` side; full rationale in
`../adr/0004-skill-improvement-log.md`.

## Where this leads

After step 4: iterate (rerun step 2 or 3), reach for `ml-modeling-autoresearch`
to keep improving the model automatically while you do other analysis, hand
`modeling/04-evaluate.md` to mattpocock's `implement` skill by hand to
productionize, or — if this graduated from a Path A quick POC into a real
project — backfill `prd/` and a full `adr/` via `ml-system-design-prd` /
`ml-system-design-high-level`. Full usage-path tables (both the modeling-focused
path and the whole-design path that forks into this one) are in
`../adr/0001-ml-modeling-family-and-continuity.md`.
