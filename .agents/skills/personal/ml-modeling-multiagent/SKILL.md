---
name: ml-modeling-multiagent
description: Use to train and compare multiple ML model candidates concurrently instead of one at a time — dispatches one subagent per candidate, then merges results. Parallel alternative to ml-modeling-train for step 3 of the ml-modeling-* chain. Trigger on "try a few models in parallel," "compare multiple algorithms at once," or "multiagent"/"concurrent" training for an ml-<topic>-<n>/ project.
---

# Train (parallel, multiple candidates)

Reads `<project-folder>/design/deep-dive.md`'s Models section (required) and `modeling/02-features.md`. Writes `<project-folder>/modeling/03-train.md` — same slot `ml-modeling-train` would write, so `ml-modeling-evaluate` doesn't need to know which one ran.

This is the sequential-vs-parallel choice from the `ml-modeling` router — pick this over `ml-modeling-train` when there are genuinely multiple reasonable candidates worth trying rather than one clear choice, or when speed matters more than sequencing (pairs naturally with Quick POC mode).

## Why this doesn't need git worktrees

Adapted from mattpocock's `implement-spec`, which dispatches one subagent per ticket into its own worktree because concurrent *code edits* to a shared repo need isolation from each other. Model candidates don't touch each other's code — they each just need their own output directory. So the isolation here is `modeling/train-candidates/<model-type>/`, not a worktree; every candidate can run directly against the current working tree.

## Process

1. **List candidates**: every model type `design/deep-dive.md`'s Models section already named, or (if it named none) the algorithm-selection matrix's short-list from `ml-modeling-train` for this data size/scenario.
2. **Dispatch concurrently**: one subagent per candidate, in the same turn (parallel tool calls, not sequential ones — the whole point is wall-clock speed). Each subagent: reads `modeling/02-features.md`, trains its one candidate, evaluates it (same metrics `ml-modeling-evaluate` would use), writes its result to `modeling/train-candidates/<model-type>/` (code + metrics), and reports its metrics back.
3. **Compare**: once all candidates report back, build a comparison table (model type, key metric, training cost/time). Pick a winner by the metric `design/deep-dive.md` named as primary — or, if the call is close, present the comparison and let the user pick rather than guessing.
4. **Write `03-train.md`**: the comparison table, the winner, and the winner's actual training code (not all candidates' code — that stays in `train-candidates/` for anyone who wants to dig in).
5. **Log**: `python3 ../ml-modeling/scripts/experiment_tracker.py log` once per candidate, so the comparison is queryable later via `compare --ids`.

Done when every candidate actually trained (not just listed as a possibility), the comparison table has real metrics per candidate — not placeholders — and `03-train.md` states why the winner won, not just which one did.
