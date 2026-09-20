---
name: ml-modeling-autoresearch
description: >-
  Run automated improvement rounds on a model that already has results —
  dispatches a couple of parallel candidates (default 2, overridable), each
  trying one focused change, keeps the winner if it beats the current best.
  Three modes: one round, until plateau, or for a duration — self-contained, no
  external scheduling. Optional follow-up after ml-modeling-evaluate, not a step
  in the sequential chain. Run by hand only, e.g. /ml-modeling-autoresearch
  ml-churn-prediction-1 until plateau, 4 candidates.
disable-model-invocation: true
---

# Autoresearch

Adapted from `karpathy/autoresearch`'s philosophy: fixed time budget per
experiment (comparable runs, not a race), one file as the edit target (scope
stays reviewable), each result kept or discarded against the running best, a
human-editable `program.md` steering the search between rounds. Not a step in
the `ml-modeling-*` sequential chain — an optional follow-up you reach for once
`modeling/04-evaluate.json` exists, usable in Regular or Quick-POC mode. Not
available in monkey-mode, which stays fully separate (see
`ml-system-design-monkey-mode`) and never gets a modeling-family follow-up.

## What one invocation does — "a round," and the 3 modes

A **round**: try a couple of new variations of the model, each within a fixed
time budget, see if any beat the current best, keep the winner or throw both
away. Every mode below is built from rounds — they differ only in how many
rounds run before the invocation stops and hands control back.

**No scheduling infrastructure is involved in any mode** — no `/loop`, no cron,
no interval, no expiry. A multi-round mode is one continuous execution that
dispatches a round, checks whether to continue, and if so dispatches the next
round immediately, entirely within that one invocation.

| Mode | Trigger words | Stops when |
|---|---|---|
| **One round** (default) | (none) | After exactly one round |
| **Until plateau** | "until plateau", "till plateau", "keep going" | Non-improvement streak hits `patience`, or `round_ceiling` (whichever first) |
| **For a duration** | "for 10 minutes", "for 1 hour", "for a duration" | Stated duration elapses, streak hits `patience`, or `round_ceiling` (whichever first) |

"For a duration" stops early on plateau too — it doesn't keep burning the rest
of the window once nothing is improving.

## How to run it

```
/ml-modeling-autoresearch <project-folder>
```
One round, by hand — run this any time you want to try again.

```
/ml-modeling-autoresearch <project-folder> until plateau
```
Keeps running rounds back-to-back, in this one invocation, until the
plateau/patience condition (or the round ceiling) is hit — then stops itself and
reports the full session.

```
/ml-modeling-autoresearch <project-folder> for 20 minutes
```
Same, but also bounded by a wall-clock duration — stops at whichever comes
first, the duration or a plateau.

**Changing how many candidates each round tries** — the default (2, or whatever
`program.md` currently says) applies unless the request says otherwise. State a
count in plain language; it composes with any mode, for this invocation only:

```
/ml-modeling-autoresearch <project-folder> 5 candidates
/ml-modeling-autoresearch <project-folder> until plateau, 4 candidates
```

This does not edit `program.md` — it's a one-off override for this invocation,
same as any other detail in the request (applies to every round the invocation
runs, not just the first). To change the *standing* default instead, edit
`program.md`'s `candidates_per_round` directly, or say so explicitly ("make 5
the new default").

## Required dependency

`modeling/04-evaluate.json` must exist — this is the "first round of results"
the whole skill assumes. Same required-dependency discipline as every other step
in this family: if it's missing, don't invent a substitute, run
`ml-modeling-evaluate` first.

## Guardrails — hard boundary, not just scope hygiene

This skill and every subagent it dispatches may write only inside
`modeling/autoresearch/`, plus the two files it's explicitly allowed to
overwrite on a genuine improvement: `modeling/04-evaluate.md` and
`04-evaluate.json`. It must **never** write to `prd/`, `adr/`, `design/`, or
`spec/` — those are the human's design-decision record, and an unattended,
repeatedly-firing loop must never be able to rewrite them, regardless of what
any round decides. This is non-negotiable, confirmed explicitly by the user who
owns this project.

**Editing while it runs.** The user may keep working on the project during a
multi-round invocation. Files the user owns and may edit freely, read fresh by
the next round: `program.md` (the steering wheel), `modeling/01-data.*`,
`02-features.md`, `03-train.md`, and anything under `design/`. Files the loop
owns and will overwrite without warning: `modeling/autoresearch/experiment.py`,
`best_metrics.json`, `rounds/`, and `modeling/04-evaluate.md`/`.json`. To change
the current-best code by hand, stop the loop (or wait for the invocation to
end), edit `experiment.py`, re-run it to refresh `best_metrics.json`, then
invoke again. State this boundary in the first message of a multi-round run.

## Scaffolding (created on first invocation)

```
modeling/autoresearch/
  program.md            human-editable config + free-text guidance (below)
  experiment.py         current best model's full train+eval code — the
                        single file every round's candidates branch from
  best_metrics.json     current best's metrics — the bar each round must clear
  rounds/round-NNNN/    one folder per round ever run, kept whether kept
                        or discarded
    candidate-<id>/     each candidate's code + metrics + a one-line verdict
    round-summary.md    which candidate (if any) won, and why
```

Seed `experiment.py`/`best_metrics.json` from whichever of
`ml-modeling-train`/`-multiagent` produced `modeling/03-train.md`'s winning
code, and from `04-evaluate.json`'s metrics.

**`program.md` format** — plain markdown, human-editable between rounds:

```markdown
# Autoresearch Program

## Config
- primary_metric: f1
- candidates_per_round: 2
- time_budget_minutes: 3
- patience: 5
- improvement_tolerance: 0.005
- round_ceiling: 50

## Guidance
(free text — edit this between rounds to redirect the search, e.g.
"focus on regularization" or "try gradient boosting next". Empty by
default; the agent picks hypotheses on its own until you steer it.)
```

Seed `primary_metric` from `04-evaluate.json`; seed the rest with the defaults
shown (adjusted per mode, see below). This file is the human's steering wheel —
read it fresh every round, don't cache stale values.

## Process

**Setup, once per invocation:** determine the mode and candidate count from the
request (table above). If "for a duration," parse the duration and mark the
start time now.

**One round** (repeated as many times as the mode requires):

1. Read `program.md`, `experiment.py`, `best_metrics.json`, and
   `design/deep-dive.md` fresh — every round, not just the first (same grounding
   every other step in this family reads; `program.md` is the human's steering
   wheel and may have been edited between rounds). If `git hash-object
   design/deep-dive.md` differs from the spec's `deep-dive-hash:` line, this
   skill does not stop to ask (it's autonomous): note `deep-dive.md changed
   since spec (<sections>)` in this round's `round-summary.md`, keep going
   against the current file, and leave the hash alone so the next interactive
   `ml-modeling-*` step asks the user (see `../ml-modeling/SKILL.md`, "Deep-dive
   changed?").
2. Dispatch `candidates_per_round` parallel subagents — same "no worktree
   needed, separate output dirs" reasoning already established for
   `ml-modeling-multiagent`, since candidates don't touch each other's code,
   just their own `rounds/round-NNNN/candidate-<id>/`. Each candidate proposes
   and tries exactly **one** focused hypothesis (a hyperparameter, a feature, a
   different model family — not a kitchen sink of unrelated changes, keeping
   each diff reviewable; don't repeat a hypothesis an earlier round already
   discarded — check `rounds/`), respecting `program.md`'s free-text guidance if
   present, trains and evaluates within `time_budget_minutes` (fixed, for
   comparability), writes its code + metrics + a one-line verdict to its own
   folder, logs itself via `../ml-modeling/scripts/experiment_tracker.py
   --log-file <project-folder>/modeling/autoresearch/experiments.json log ...`
   (always pass `--log-file`, before the subcommand; the default is
   CWD-relative), and reports its metric back.
3. Compare the round's best candidate against `best_metrics.json`'s
   `primary_metric`, using `improvement_tolerance` (default 0.5% relative) so
   noise-level wiggle doesn't count as an improvement.
   - **Improved**: promote — overwrite `experiment.py`, `best_metrics.json`, and
     `modeling/04-evaluate.md`/`.json` too. The dashboard's Final Results tab
     picks this up automatically, zero dashboard code involved. Reset the
     non-improvement streak to 0. **A winning candidate's script lives 3
     directories deeper than `experiment.py`'s promoted location**
     (`rounds/round-NNNN/candidate-<id>/` vs. `autoresearch/`) — if it computes
     its data path relative to its own file location (e.g.
     `Path(__file__).resolve().parents[N]`), that `N` is wrong once copied up
     and must be adjusted for the new depth. Re-run the promoted file from its
     real location and confirm it still produces the same metrics before
     trusting it as current best — don't just copy and assume.
   - **Not improved**: discard the code (stays in `rounds/` for the record);
     current best and streak both unchanged except the streak increments by 1.
4. Write `round-summary.md` (state the candidate count used, since it can vary
   invocation to invocation).

**After each round, in a multi-round mode**, check the stop conditions from the
table above (streak vs. `patience`, round count vs. `round_ceiling`, elapsed
time vs. the requested duration if any). If none are met, go straight to another
round — no pause, no waiting for the human. If one is met, stop.

**At the end of the invocation** (whichever mode), report to the user: every
round's outcome in the session (kept or discarded, old metric → new metric where
kept), the final non-improvement streak against `patience`, and which stop
condition ended the session (or, for one-round mode, that it's just done). No
`/loop` command, no "recommend stopping" — in a multi-round mode, this
invocation already stopped itself; to do more, invoke again.

## Stopping — plateau-based, and self-enforced

Round duration scales with model complexity and data size, so a fixed time or
iteration budget means something different per project — a duration is available
when you want one, but plateau detection is what actually knows when a search
has stopped paying off. Track the streak of consecutive rounds with no
improvement over `best_metrics.json` beyond `improvement_tolerance`. In "until
plateau" or "for a duration" mode, hitting `patience` (default 5) or
`round_ceiling` (default 50, pure safety backstop) **actually ends the session**
— this skill now owns its own recurrence, so there's no external loop to leave
running or unsubscribe from. Report the streak in the final summary regardless
of what stopped the session, so it's always clear whether it plateaued, ran out
of time, or hit the round ceiling.

## Regular vs. Quick-POC mode

Both work — keyword-selected same as the rest of the family
("poc"/"quick"/"mvp"/"fast" vs. "regular"/nothing).

- **Regular**: cross-validation within each candidate's evaluation, longer
  default `time_budget_minutes` — more rigorous, slower throughput.
- **Quick POC**: single train/test split, shorter default `time_budget_minutes`
  — matches the family's one-hour-MVP spirit elsewhere.

Done when every round's outcome (kept or discarded, with real metrics either
way) is reported, `rounds/round-NNNN/` has every candidate's real code and
metrics (not placeholders) for every round the invocation ran,
`program.md`/`best_metrics.json` reflect the true current state, and the closing
message states which stop condition ended the session and the final streak. Full
design rationale in `../adr/0003-autoresearch.md` (why parallel candidates
instead of karpathy's single-threaded design, the hard write boundary) and
`../adr/0005-autoresearch-self-contained-looping.md` (why recurrence is
self-contained, not delegated to external scheduling).

If this run turns up a bug or a better design in this skill, or you ask for a
change to how it works, log it — see `../ml-modeling/SKILL.md`'s Skill
improvement log.
