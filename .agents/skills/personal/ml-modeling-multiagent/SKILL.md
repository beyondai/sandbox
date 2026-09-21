---
name: ml-modeling-multiagent
description: >-
  Use to train and compare multiple ML model candidates concurrently instead of
  one at a time — dispatches one subagent per candidate, then merges results.
  Parallel alternative to ml-modeling-train for step 3 of the ml-modeling-*
  chain. Trigger on "try a few models in parallel," "compare multiple algorithms
  at once," or "multiagent"/"concurrent" training for an ml-<topic>-<n>/
  project.
---

# Train (parallel, multiple candidates)

Reads `<project-folder>/design/high-level.md`'s Phasing (model class per phase),
`modeling/01-data.md` (class balance), and `modeling/02-features.md`. Writes
`<project-folder>/modeling/03-train.md` — same slot `ml-modeling-train` would
write, so `ml-modeling-evaluate` doesn't need to know which one ran. Project folder and output format: see `../ml-modeling/SKILL.md`,
"Which project folder" and "Output docs". First, run the
"Design docs changed?" check from `../ml-modeling/SKILL.md`.

Train on `02-features.md`'s "Output table" if present, else `01-data.json`
-> `dataset.train`; pass that table path to every candidate subagent's
prompt. Each candidate cross-validates inside that table only;
`dataset.test` is never read here - it belongs to `ml-modeling-evaluate`.

This is the sequential-vs-parallel choice from the `ml-modeling` router — pick
this over `ml-modeling-train` when there are genuinely multiple reasonable
candidates worth trying rather than one clear choice, or when speed matters more
than sequencing (pairs naturally with Quick POC mode).

## Why this doesn't need git worktrees

Adapted from mattpocock's `implement-spec`, which dispatches one subagent per
ticket into its own worktree because concurrent *code edits* to a shared repo
need isolation from each other. Model candidates don't touch each other's code —
they each just need their own output directory. So the isolation here is
`modeling/train-candidates/<model-type>/`, not a worktree; every candidate can
run directly against the current working tree.

## Process

1. **List candidates**: every model class high-level's Phasing named across
   its phases, plus the algorithm-selection matrix's short-list from
   `ml-modeling-train` for this data size/scenario if Phasing named only one.
2. **Dispatch concurrently**: one subagent per candidate, in the same turn
   (parallel tool calls, not sequential ones — the whole point is wall-clock
   speed). Each subagent: reads `modeling/02-features.md`, trains its one
   candidate, evaluates it (same metrics `ml-modeling-evaluate` would use),
   writes its result to `modeling/train-candidates/<model-type>/` (code +
   metrics), and reports its metrics back.
3. **Compare**: once all candidates report back, build a comparison table (model
   type, key metric, training cost/time). Pick a winner by the primary metric
   `prd/<topic>.md`'s Metrics — offline section names — or, if the call is
   close, present the comparison and let the user pick rather than guessing.
4. **Write `03-train.md`**: the comparison table, the winner, and the winner's
   actual training code (not all candidates' code — that stays in
   `train-candidates/` for anyone who wants to dig in).
5. **Log**: `python3 ../ml-modeling/scripts/experiment_tracker.py --log-file
   <project-folder>/modeling/experiments.json log ...` once per candidate, so
   the comparison is queryable later via `compare --ids`. Always pass
   `--log-file`, before the subcommand (the default is CWD-relative and would
   scatter logs across projects).

Done when every candidate actually trained (not just listed as a possibility),
the comparison table has real metrics per candidate — not placeholders — and
`03-train.md` states why the winner won, not just which one did.

If this run turns up a bug or a better design in this skill, or you ask for a
change to how it works, log it — see `../ml-modeling/SKILL.md`'s Skill
improvement log.
