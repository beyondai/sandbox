# ml-system-design-* / ml-modeling-* - operational reference

Contents: Design principles | Monkey-mode | Monkey-MLP | Autoresearch | Skill
improvement log | Design drift: detect, then ask | Dashboard | Running things
concurrently | When a git worktree earns its keep | ADR index

Entry point for a new project: `/ml-system-design <topic> [poc]`. Read
`docs/ML-SKILLS-GUIDE.md` first for orientation. This file holds the
detail that guide deliberately leaves out: how the pieces behave when several
things run at once, the mechanics behind the drift check and the improvement
log, autoresearch's modes, and when a git worktree is and is not worth it.
Rationale for each decision is in `adr/`. Style rules for skill files and docs, and
how to check them: `docs/SKILL-STYLE-GUIDE.md`.

## Design principles

`ml-design-principles.md` is the single source of truth for the principles.
The design and modeling skills apply them; the critique catalogs check them.
Each principle has a table of the skills that use it.

| # | Principle | Applied in | Checked by |
|---|---|---|---|
| 1 | Simple by default, complex only with evidence | definition, high-level, deep-dive, train, multiagent | the complexity gate in both lenses |
| 2 | The intended behavior, not the metric | prd, definition, evaluate (output review) | sys B7, mod I12 |
| 3 | A proven version ships, and it keeps up with change | high-level (gates, plan B), deep-dive (retrain cadence), delivery (staged rollout, Retraining) | sys H2, H3, I5, F7 |

To add a principle, follow the steps at the top of that file, then update
this table, `docs/ML-SKILLS-GUIDE.md`, and `docs/ml-design-template.md`.

## Monkey-mode

A separate, user-invoked, background track. Ask up to three questions, then
build and evaluate in the background while the design work continues. It
never blocks - unanswered questions fall back to self-inferred defaults:

| # | Question | Fallback if unanswered |
|---|---|---|
| 1 | Task + data | Task type read from the prompt; small synthetic dataset if no data is referenced |
| 2 | Primary metric | Standard metric for the task (F1 / RMSE / nDCG) |
| 3 | Success bar | An assumed target number based on problem and data, not just "beat random" |

Writes only `monkey-mode/report.md`. Reads nothing under `design/`, `prd/`,
or `modeling/`. Detail: `ml-system-design-monkey-mode/SKILL.md`.

## Monkey-MLP

A sibling of monkey-mode, same three-question/never-blocks contract, for
tasks with high-cardinality identity columns (user/item ids,
recommendation-shaped problems) where a learned embedding is a better fit
than one-hot + a tree model. Writes only `monkey-mlp/report.md`, disjoint
from `monkey-mode/report.md`, so both can run in the same project folder for
a direct comparison. Two eval rules are non-negotiable (unlike the rest of
its fast defaults): early stopping is chosen from an internal validation
split carved out of train only, never from the test set, and the test set is
scored exactly once - skipping either silently inflates the reported AUC (a
real leak of ~0.004 AUC was caught and fixed this way on the KKBOX project).
Detail: `ml-system-design-monkey-mlp/SKILL.md`.

## Autoresearch

Optional follow-up once `modeling/04-evaluate.json` exists. User-invoked
only. Self-contained: no `/loop`, no cron, no interval, no expiry. One
mechanic - run a round, check whether to continue, run another round
immediately if so - in three modes:

| Mode | Command | Stops when |
|---|---|---|
| One round | `/ml-modeling-autoresearch <project>` | After that round |
| Until plateau | `... until plateau` | Non-improvement streak hits `patience`, or the round ceiling |
| For a duration | `... for 20 minutes` | Duration elapses, streak hits `patience`, or round ceiling - whichever first |
| Any mode + count | `... until plateau, 4 candidates` | Same as the mode chosen |

Default candidates per round is 2 (`program.md`'s `candidates_per_round`).
Stopping is plateau-based because round duration scales with model and data
size, so a fixed count means something different per project. Autoresearch
writes only inside `modeling/autoresearch/` plus `04-evaluate.md`/`.json` -
never `prd/`, `adr/`, `design/`, or `spec/`. Detail:
`ml-modeling-autoresearch/SKILL.md`, `adr/0003`, `adr/0005`.

## Skill improvement log

Any skill in either family can log a proposed change to *itself* (not to the
project it is working on) in the one shared log,
`.agents/skills/personal/SKILL-IMPROVEMENTS.md`:

```markdown
## <date> - <skill-name>
- **Project**: <project folder where it was found>
- **Source**: agent-found bug | agent-found better design | user-requested
- **Status**: proposed
- **Finding**: <what's wrong or what could be better, concretely>
- **Suggested change**: <the edit, concrete enough to apply as-is>
```

An agent-found entry needs evidence that the skill made the work worse (a
missed, wrong, or late result, or extra work for the user); a gap that the
skill covered anyway is noise (`adr/0019`).

Entries are appended, never overwritten or deleted. Nothing is applied
automatically: a `SKILL.md` is shared by every future project, so a silent
edit from one run would change behavior everywhere. At the end of a run, any
skill checks for `proposed` entries and offers a review; adopting one applies
the edit to `.agents/skills/personal/<skill>/SKILL.md` and flips the entry to
`adopted` (or `declined`), with an "Applied to" note. At the end of every
session that used an ml-* skill, the agent also reflects on the whole
session, logs new skill issues, and offers the review (the sandbox
`CLAUDE.md` has the same rule). Older entries stay in
`labs/<project>/SKILL-IMPROVEMENTS.md` as history. Rationale: `adr/0004`,
`adr/0016`.

## Design drift: detect, then ask

When `ml-modeling-*` first runs against a project, it synthesizes
`spec/<topic>.md` from `prd/` + `adr/` + `design/high-level.md`, with
`prd-hash:` and `high-level-hash:` as its first lines (`git hash-object -w
<file>`; `-w` stores the blob so the diff stays available even if that
version was never committed).

Every step runs `ml-modeling/scripts/spec_hash_check.sh <project>` before
its own work. On a mismatch it
shows the diff, summarized to which sections moved, and asks two questions:
re-synthesize the spec or keep it; apply the changed decisions going forward
or proceed on the old ones. The answer is recorded as one line in the step's
`.md`. If the change is applied, the hash is refreshed; if not, the next step
asks again - each step is a fresh chance to pick the change up. Autoresearch
never asks: it notes the change in `round-summary.md` and the next
interactive step raises it.

Corrections that flow the other way - execution shows the framing, a source,
or the phasing was wrong - are offered back to `design/high-level.md` (hash
refreshed afterward). Step-level decisions (features chosen, model picked,
split used) stay in the step's own `.md`; on the hands-on route, those files
are the deep dive's record.

## Dashboard

`ml-modeling-data` copies `ml-modeling-data/assets/dashboard_app.py` to
`<project>/dashboard/app.py` once. It is a generic reader of
`../modeling/01-data.json`, `../modeling/04-evaluate.json`, and
`../modeling/train-candidates/*/metrics.json`; no project edits it. To change
the design, edit the asset and re-copy. Two sections only (EDA, final
results) plus a model comparison when multiagent ran - feature and training
detail stay in their `.md` files. Rationale: `adr/0002`.

Each project gets its own Streamlit port: the first free port from 8501 up,
written to `dashboard/.port`, with the PID in `dashboard/.pid`.
`ml-modeling-data/scripts/launch_dashboard.sh` does this, and reuses a
running dashboard. It kills or reuses only its own streamlit process.
`ml-modeling-evaluate` runs it again, and never checks bare `:8501`.

## Running things concurrently

Runs that naturally overlap never write the same files. Isolation is the
folder split, not a git checkout:

| Pattern | Writes | Shared |
|---|---|---|
| Design path + monkey-mode, one project | `design/`, `prd/`, `adr/` vs. `monkey-mode/` | the shared `SKILL-IMPROVEMENTS.md` (append-only) |
| Monkey-mode + monkey-mlp, one project | `monkey-mode/` vs. `monkey-mlp/` | the shared `SKILL-IMPROVEMENTS.md` (append-only) |
| Design continues while `ml-modeling-*` runs | `design/`, `prd/` vs. `modeling/`, `spec/`, `dashboard/` | `prd/<topic>.md`, `design/high-level.md` - read by every modeling step, hence the drift check |
| You edit by hand while autoresearch loops | Yours: `program.md`, `modeling/01-03*`, `design/`. The loop's: `autoresearch/experiment.py`, `best_metrics.json`, `rounds/`, `04-evaluate.*` | Nothing, if each side stays on its side |
| Two projects at once | Two disjoint folders | Only process/git state: dashboard port, git index |

Three mechanics keep the shared bits apart: the per-project dashboard port
(above); every `experiment_tracker.py` call passes `--log-file
<project>/modeling/experiments.json` (its default is CWD-relative, and the
agent's CWD is wherever it happened to be); and the drift check (above).

One git rule for any agent in a shared working tree: never run `git stash`,
`checkout`, `restore`, `reset`, or `clean`. Those discard uncommitted files,
and in a shared tree some of them belong to another session.

## When a git worktree earns its keep

Only when two projects need independent commit histories while both are
mid-flight (separate branches, separate index). Use Claude Code's
`EnterWorktree`, or `Agent(isolation: "worktree")` for a background run, on
demand; no standing setup. Costs: `.venv` is gitignored, so `uv sync` again;
`data/`, `*.csv`, `*.pkl`, `models/` are gitignored, so an existing project's
data and trained models are absent in the new tree; Claude Code keys
permissions and memory by directory path, so prompts start fresh; and
anything uncommitted on `main` (a skill mid-edit) is invisible there. Skill
edits stay on `main` regardless.

## ADR index

| ADR | Decision |
|---|---|
| 0001 | Two families with a file-based handoff; spec shape; sequential vs. parallel training |
| 0002 | Dashboard scope: EDA + results only, generic reader, per-project port |
| 0003 | Autoresearch as an opt-in extra after evaluate |
| 0004 | Skill improvement log: per-project, log-and-review, never auto-apply |
| 0005 | Autoresearch self-contained looping (no `/loop`) |
| 0006 | Fork after high-level; deep-dive and ml-modeling are alternatives |
| 0007 | Cleaning is a phase inside `ml-modeling-data`, not a new step |
| 0008 | Monkey-MLP: sibling skill to monkey-mode, not a model option on it |
| 0009 | ml-critique: a core with system and modeling lenses, 2 modes |
| 0010 | One folder per project, parent `labs/` unless the user names one |
| 0011 | Skill-writing guides: Check step, scripts, checklists, TOCs |
| 0012 | One shared reference for negatives, architecture, training setup |
| 0013 | Serving on both routes: deep-dive item + `ml-modeling-serve` step 5 |
| 0014 | Style guide; `check_skill_style.py` and `check_docs.py`; when to run them |
| 0015 | Anthropic skill checklist: evals per family, named constants, 3 more checks |
| 0016 | One shared skill improvement log; reflect at the end of every session |
| 0017 | Ranking path, proxy rule, chain mode, bench --full, from the Riot wiki session |
| 0018 | Critique: full coverage, sort key, Quick mode (2 hours), critique context, view asked each run |
| 0019 | Critique questions give why and what changes; log only issues with evidence |
| 0020 | Critique: one mode, `ml-critique-merge`, `ml-critique-share-out`, `[user]` tag, Done well rule |
| 0021 | Critique: share-out never cuts a P1, one meaning for `[C]`, Done well and context in the Checks |
| 0022 | Principle 2 (the intended behavior, not the metric), retrain fits the change cadence, fuller phase gates |
| 0023 | Principle 2 skill-check fixes (the PRD keeps no checklist copy), Principle 3, delivery Retraining item, markdown template |
