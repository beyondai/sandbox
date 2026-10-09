---
name: ml-modeling-autoresearch
description: >-
  Run automated improvement rounds on a model that already has results -
  dispatches a couple of parallel candidates (default 2, overridable), each
  trying one focused change, keeps the winner if it beats the current best.
  Three modes: one round, until plateau, or for a duration - self-contained, no
  external scheduling. Optional follow-up after ml-modeling-evaluate, not a step
  in the sequential chain. Run by hand only, e.g. /ml-modeling-autoresearch
  ml-churn-prediction-1 until plateau, 4 candidates.
disable-model-invocation: true
---

# Autoresearch

Contents: Modes | Write boundary (hard rule) | Scaffolding (first invocation) |
Steps | Check

Based on `karpathy/autoresearch`: a fixed time budget for each experiment,
one file as the edit target, each result kept or discarded against the
running best, and a `program.md` that the user edits to steer the search.

- An optional follow-up, not a step in the chain. Regular and Quick POC.
  Never in monkey-mode.
- **Requires** `modeling/04-evaluate.json`. If it is missing, run
  `ml-modeling-evaluate` first. Do not make a substitute.
- **Rules:** `../ml-system-design/SKILL.md`, "Project folder" and "Output
  docs". Reasons: `../adr/0003-autoresearch.md` (parallel candidates, the
  write boundary), `../adr/0005-autoresearch-self-contained-looping.md`
  (no external scheduling).

## Modes

A **round**: a few candidates each try one change within a fixed time
budget. The best one is kept if it beats the current best. Each mode is a
number of rounds in one invocation. There is no `/loop`, no cron, and no
interval: the next round starts at once.

| Mode | Trigger words | Stops when (first one) |
|---|---|---|
| One round (default) | none | 1 round is done |
| Until plateau | "until plateau", "till plateau", "keep going" | the streak reaches `patience`, or `round_ceiling` |
| For a duration | "for 10 minutes", "for 1 hour", "for a duration" | the time ends, the streak reaches `patience`, or `round_ceiling` |

```
/ml-modeling-autoresearch <project-folder>
/ml-modeling-autoresearch <project-folder> until plateau, 4 candidates
/ml-modeling-autoresearch <project-folder> for 20 minutes
```

- "N candidates" in the request applies to each round of this invocation
  only. It does not edit `program.md`. To change the default, edit
  `candidates_per_round`, or the user says "make 5 the new default".
- Quick POC (keywords: "Regular and Quick-POC mode" in
  `../ml-system-design/SKILL.md`): one train/test split, a
  shorter `time_budget_minutes`. Regular: CV in each candidate, a longer
  budget.

## Write boundary (hard rule)

The skill and each subagent write only in `modeling/autoresearch/`, plus
`modeling/04-evaluate.md` and `.json` on a real improvement. Never write
to `prd/`, `adr/`, `design/`, `spec/`, or `SKILL-IMPROVEMENTS.md`. Those
files are the user's decision record, and an unattended loop must never
rewrite them. The user confirmed this rule.

State this in the first message of a multi-round run:
- **The user can edit** (the next round reads them): `program.md`,
  `modeling/01-data.*`, `02-features.md`, `03-train.md`, `design/`.
- **The loop overwrites:** `experiment.py`, `best_metrics.json`,
  `rounds/`, `04-evaluate.md` and `.json`.
- To change the current best by hand: stop the loop, edit
  `experiment.py`, run it to refresh `best_metrics.json`, and start again.

## Scaffolding (first invocation)

```
modeling/autoresearch/
  program.md            config + guidance; the user edits it
  experiment.py         the current best train+eval code; each candidate
                        starts from it
  best_metrics.json     the current best; the bar for each round
  rounds/round-NNNN/    one folder for each round, kept or discarded
    candidate-<id>/     code + metrics + a one-line verdict
    round-summary.md    the winner (if any), why, and the Check result
```

Seed `experiment.py` from the winning code in `03-train.md`, and
`best_metrics.json` from `04-evaluate.json`.

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
(free text - edit this between rounds to redirect the search, e.g.
"focus on regularization" or "try gradient boosting next". Empty by
default; the agent picks hypotheses on its own until you steer it.)
```

Seed `primary_metric` from `04-evaluate.json`. Use the other defaults,
adjusted for the mode (Quick POC: a shorter `time_budget_minutes`).

## Steps

Progress (copy into your reply, tick each line in each round):

```
[ ] Setup: mode, candidate count, start time
[ ] Round N: 1 read  2 dispatch  3 compare/promote  4 summary
[ ] Stop condition met? -> next round, or end report
[ ] Check (each round, and the end report)
```

**Setup.** Get the mode and the candidate count from the request. For a
duration, record the start time.

**One round:**
1. **Read** these files again (they can change between rounds):
   `program.md`, `experiment.py`, `best_metrics.json`, `prd/<topic>.md`,
   `design/high-level.md`. Run:

   ```
   bash .agents/skills/personal/ml-modeling/scripts/spec_hash_check.sh <project-folder>
   ```

   On `CHANGED`, do not ask and do not refresh. Write
   `<file> changed since spec (<sections>)` in `round-summary.md`, and
   continue. On `NOHASH`, `MISSING`, or exit 2, record it the same way and
   continue with the files as they are.
2. **Dispatch** `candidates_per_round` subagents in parallel. Each writes
   only to `rounds/round-NNNN/candidate-<id>/`. Each candidate:
   - tries exactly one hypothesis (a hyperparameter, a feature, or a model
     family), so each diff stays reviewable, and not one that `rounds/`
     shows was discarded;
   - follows the Guidance in `program.md`;
   - trains and evaluates within `time_budget_minutes` (fixed, so the
     candidates are comparable);
   - writes code, metrics, and a one-line verdict;
   - logs itself (`--log-file` before the subcommand):

     ```
     python3 .agents/skills/personal/ml-modeling/scripts/experiment_tracker.py \
       --log-file <project-folder>/modeling/autoresearch/experiments.json log ...
     ```

   - reports its metric.
3. **Compare** the best candidate with `best_metrics.json` on
   `primary_metric`. An improvement must be larger than
   `improvement_tolerance` (relative).
   - **Improved:** promote. Overwrite `experiment.py`,
     `best_metrics.json`, and `04-evaluate.md` and `.json`. The dashboard
     shows it with no code change. Set the streak to 0.
     - The candidate script is 3 folders deeper than `experiment.py`. If
       it computes paths from its own location (for example
       `Path(__file__).resolve().parents[N]`), correct `N`.
     - Run the promoted `experiment.py` from its real location. Confirm
       that it gives the same metrics.
   - **Not improved:** keep the code in `rounds/` only. Add 1 to the
     streak.
4. **Summary and Check.** Write `round-summary.md` with the candidate
   count. Then do the Check (below).

**After each round** (multi-round modes): check the stop conditions. If
none is met, start the next round at once. Do not wait for the user.

**End report:** each round's result (kept or discarded, old -> new
metric), the final streak against `patience`, and the stop condition. To
do more, the user runs the skill again.

Plateau is the main stop signal: round time changes with the model and
the data, so a fixed count means different things in each project.
`round_ceiling` is only a safety limit.

## Check

Do "Check the output" in `../ml-system-design/SKILL.md`, with 2 changes:
the skill does not ask the user, and it writes the result and each skill
issue in `round-summary.md` (not in `SKILL-IMPROVEMENTS.md`). Intent
questions:
1. Does each candidate test one hypothesis, with real code and metrics
   (no placeholders)?
2. Is each promotion larger than `improvement_tolerance`, and confirmed by
   a run of the promoted `experiment.py`?
3. Do `program.md`, `best_metrics.json`, and `04-evaluate.json` show the
   true current state?
4. Did all writes stay inside the write boundary?

Done when the 4 answers are yes for each round, `check_doc.py` prints
`OK` for `round-summary.md` and `04-evaluate.md`, and the end report gives
the stop condition and the final streak. In the end report, list the
skill issues from the round summaries, and offer to log them.
