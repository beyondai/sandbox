# ml-modeling-* family, and how it chains to ml-system-design-*

> **2026-09-20:** the fork point moved from `design/deep-dive.md` to
> `design/high-level.md`, and deep-dive and `ml-modeling-*` became
> alternatives rather than a sequence — see `0006-fork-after-high-level.md`.
> The Usage-path tables and the first Consequence below are kept as history.

The `ml-system-design-*` family covers deciding and documenting an ML system's design (PRD → high-level → deep-dive → delivery → post-delivery) but stops at decisions on paper — it never executes anything. `ml-modeling-*` is a new, separate family that picks up from `ml-system-design-deep-dive`'s decisions and actually runs the data→features→train→evaluate work, checkpointed at each step. Kept as a separate family rather than nested under deep-dive so "decide & document" stays distinct from "actually execute," but the two need a real, file-based handoff — not just conversation memory — since either family can be invoked standalone in a fresh session.

Source material for `ml-modeling-*`: `ds-modeling-SKILL.md` (`borghei/Claude-Skills`, `data-analytics/data-scientist/`), rewritten for this repo's conventions (minimal frontmatter, no references to agents/tooling that don't exist here) and split into one skill per step. Three of its referenced CLI tools (`experiment_tracker.py`, `feature_selector.py`, `hypothesis_tester.py`) were ported near-verbatim from the same source repo — they're stdlib-only, no adaptation needed beyond confirming they run.

## Project-folder layout

Extends the existing `ml-<topic>-<n>/` convention (`prd/`, `adr/`, established by `ml-system-design-prd`) with two new subfolders:

```
ml-<topic>-<n>/
  prd/<topic>.md              existing
  adr/000N-*.md                 existing pattern, now formalized: any ml-system-design-* stage
                                  offers one when a decision meets domain-modeling's 3 criteria
                                  (hard to reverse, surprising, real tradeoff)
  design/
    deep-dive.md                  NEW — ml-system-design-deep-dive writes here
  spec/<topic>.md                  NEW — design→modeling fork point (see below)
  modeling/
    01-data.md                     ml-modeling-data
    02-features.md                   ml-modeling-features
    03-train.md                        ml-modeling-train (sequential) OR
                                         ml-modeling-multiagent (parallel) — same slot
    04-evaluate.md                       ml-modeling-evaluate — reads 03-train.md either way
```

`spec/<topic>.md` is a synthesis of `prd/` + `adr/` + `design/deep-dive.md` into an implementation-ready doc, shaped like mattpocock's `to-spec` template (Problem Statement, Solution, Implementation Decisions, Testing Decisions, Out of Scope) — reusing that shape without calling that skill (see Considered Options). Produced by the `ml-modeling` router the first time any `ml-modeling-*` step runs against a project that has `design/deep-dive.md` but no `spec/` yet.

## Regular vs. Quick-POC mode

Both families get both modes:

- **Regular**: ask when unknown, never invent; full checklist rigor.
- **Quick POC — a one-hour MVP**, not "less documentation": `ml-system-design-deep-dive` asks its essential questions in one batched pass (not grilling rounds) and states defaults for the rest, producing a real but surface-level `design/deep-dive.md` fast. `ml-modeling-*` still always reads `design/deep-dive.md` in both modes — POC mode does not let it run standalone — but favors speed once running: fewer clarifying questions, first-reasonable-choice over exhaustive comparison.

Mode is selected by keyword in whatever the user types (no structured flag syntax anywhere in this skill family):

| Words in the request | Mode |
|---|---|
| "poc", "quick", "mvp", "prototype", "fast", "one hour"/"1 hour" | Quick POC |
| "regular", "full", or no mode word at all | Regular (default) |

## Sequential vs. parallel training

`ml-modeling-train`: one model candidate, sequential, checkpointed — unchanged shape from a normal step skill.

`ml-modeling-multiagent`: same inputs (`modeling/02-features.md` + deep-dive's Models section) and same output slot (`modeling/03-train.md`), different strategy — dispatches one concurrent subagent per candidate model type, each training and self-evaluating independently into its own `modeling/train-candidates/<model-type>/` path, then compares metrics and writes the single `03-train.md` (comparison table + winner + its code). Adapts `implement-spec`'s concurrent-subagent pattern rather than copying it: that skill needs git worktrees because concurrent *code edits* to a shared repo need isolation; concurrent *model candidates* don't touch each other's code, so no worktree machinery is needed here. The user picks which to run per-invocation via the same keyword mechanism as mode ("sequential" vs. "parallel"/"multiagent"); nothing downstream (`ml-modeling-evaluate`) needs to know which one ran.

## Usage paths

**Path A — modeling-focused (one-hour MVP):**

| Step | Command | Reads | Writes |
|---|---|---|---|
| 1 | `/ml-system-design-deep-dive` (POC) | — | `design/deep-dive.md` |
| 2 | `/ml-modeling-data` | `design/deep-dive.md` | `modeling/01-data.md` |
| 3 | `/ml-modeling-features` | `modeling/01-data.md` | `modeling/02-features.md` |
| 4 | `/ml-modeling-train` or `/ml-modeling-multiagent` | `modeling/02-features.md` | `modeling/03-train.md` |
| 5 | `/ml-modeling-evaluate` | `modeling/03-train.md` | `modeling/04-evaluate.md` |

Ends with a working, evaluated model in ~1 hour. Next: iterate (back to step 3/4), hand `modeling/04-evaluate.md` to mattpocock's `implement` by hand to productionize, or backfill `prd/`/full `adr/` via Path B if this graduates into a real project.

**Path B — whole MLE system design (can fork into modeling):**

| Step | Command | Writes |
|---|---|---|
| 1 | `/ml-system-design-prd <topic>` | `prd/<topic>.md` |
| 2 | `/ml-system-design-high-level` | design content; offers an ADR on a real tradeoff |
| 3 | `/ml-system-design-deep-dive` (Regular) | `design/deep-dive.md` |
| fork | first `ml-modeling-*` call | `spec/<topic>.md`, then Path A steps 2-5 |
| 4 | `/ml-system-design-delivery` | design content — Eval references real `04-evaluate.md` if forked |
| 5 | `/ml-system-design-post-delivery` | design content |

Ends with a full design doc (prd + adr + design + spec, optionally + modeling) ready for review or handoff.

## Considered Options

Checked whether `ml-modeling-*` should call or fork mattpocock's `to-spec`, `implement`, and `implement-spec` instead of the ml-series producing its own PRD/ADR/spec artifacts:

- `to-spec` synthesizes existing conversation into a spec and publishes to an issue tracker — external system, not a repo file, and explicitly "no interview." Doesn't overlap with `ml-system-design-prd`, which is interview-driven and writes into this repo's project-folder convention.
- `implement-spec` is a concurrent multi-agent orchestrator built for a parallel *ticket graph* with blocking edges — the opposite shape from our strictly sequential data→features→train→evaluate chain. `ml-modeling-multiagent` adapts its concurrent-subagent mechanic for a genuinely parallel unit (independent model candidates) rather than forcing our sequential chain through a ticket-graph shape.
- `implement` is small and generic enough (no location assumptions) that it doesn't need integration — a user can point it at `modeling/04-evaluate.md` by hand later. Decided not to wire this automatically; kept as a documented next-step in Path A instead.

Rejected: forking adapted versions of `to-spec`/`implement-spec` into the ml-series. Both are shaped around conventions (issue tracker, ticket graph) that fight the project-folder/sequential conventions here — forking either would mean stripping out most of what makes them useful, ending up as a rewrite in disguise rather than a reuse.

## Consequences

- `ml-system-design-deep-dive` goes from writing nothing to being a required upstream dependency for the entire `ml-modeling-*` family — if that file is missing or stale, every modeling step's grounding is stale too.
- Two ways to produce `modeling/03-train.md` (sequential vs. parallel) means `ml-modeling-evaluate` must handle both shapes of its input without caring which one ran — this contract lives in this ADR and in `ml-modeling-evaluate`'s own instructions, not enforced by tooling.
- `spec/<topic>.md` is a fourth artifact type (alongside PRD, ADR, and the deep-dive decisions file) with no existing precedent in this repo before now — its template is borrowed from mattpocock's `to-spec` shape specifically so it stays recognizable if the user ever does hand it to that skill or to `implement`.
