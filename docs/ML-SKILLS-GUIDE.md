# ML Skills Guide

A skimmable orientation to the `ml-system-design-*` / `ml-modeling-*` skill
family in `.agents/skills/personal/`: designing an ML system, executing a
hands-on modeling pipeline, and a fast autonomous baseline mode, all chained
through files in a project folder rather than conversation memory — so any
step can be resumed standalone, in a fresh session, by anyone who just opens
the right file.

## How it works — the rhythm

Every step is the same shape: **invoke → it writes a file → you read that
file → invoke the next step**, which reads what the previous one wrote.
Nothing depends on scrollback.

```
/ml-modeling-data churn dataset
  → writes modeling/01-data.md
(you check modeling/01-data.md)
/ml-modeling-features
  → reads 01-data.md, writes modeling/02-features.md
```

## The shape

```
topic/prompt
  │
  ├─▶ /ml-system-design-monkey-mode  (early, independent fork)
  │     3 Qs, self-inferred fallback if unanswered
  │     → monkey-mode/report.md  (done — nothing else touches this)
  │
  ▼
(new project? ask first: monkey-mode in parallel? PRD first?)
  │
  ▼
/ml-system-design-prd  (whole design path)
  │
  ▼
-high-level  → design/high-level.md  (offers an ADR on real tradeoffs)
  │
  ▼
-deep-dive  → design/deep-dive.md
  │
  ▼  FORK into execution
ml-modeling-data → -features
  │
  ├─▶ ml-modeling-train        (sequential, 1 model)
  ├─▶ ml-modeling-multiagent   (parallel, N candidates)
  │     both write modeling/03-train.md  — CONVERGE here
  ▼
ml-modeling-evaluate → modeling/04-evaluate.md
  │
  ▼  CONVERGE back into the design doc
-delivery  (cites real eval results if modeling ran)
  │
  ▼
-post-delivery
```

Three things worth naming explicitly:

- **The design path forks into execution** at `design/deep-dive.md` —
  `ml-modeling-*` reads it, always, in both Regular and Quick-POC mode.
- **Training forks again, then converges** — sequential (`ml-modeling-train`)
  or parallel (`ml-modeling-multiagent`) both write the same
  `modeling/03-train.md` slot, so `ml-modeling-evaluate` doesn't care which
  one ran.
- **Monkey-mode is not part of this graph at all** — it shares only the
  project-folder root, nothing else. No dependency on `design/deep-dive.md`,
  no write into `modeling/`.

## Monkey-mode

A fully separate, user-invoked, background-dispatched fast-baseline track.
Ask up to 3 questions, then build and evaluate in the background while you
keep working on the real design. It never blocks — unanswered questions fall
back to self-inferred defaults:

| # | Question | If unanswered — self-inferred fallback |
|---|---|---|
| 1 | Task + data | Task type read from the prompt's wording; small synthetic dataset generated if no real data is referenced |
| 2 | Primary metric | Standard metric for the inferred task (F1 / RMSE / nDCG) |
| 3 | Success bar | An actual assumed target number based on the problem + data, not just "beat random" |

Full detail: `.agents/skills/personal/ml-system-design-monkey-mode/SKILL.md`.

## Autoresearch

Optional follow-up once `modeling/04-evaluate.json` exists — user-invoked
only, not a step in the chain. Self-contained: no `/loop`, no cron, no
interval, no expiry. Three modes, one mechanic — run a round, check whether
to continue, run another round immediately if so, all within one invocation:

| Mode | Command | Stops when |
|---|---|---|
| One round | `/ml-modeling-autoresearch <project>` | After that one round |
| Until plateau | `/ml-modeling-autoresearch <project> until plateau` | Non-improvement streak hits `patience`, or round ceiling |
| For a duration | `/ml-modeling-autoresearch <project> for 20 minutes` | Duration elapses, streak hits `patience`, or round ceiling — whichever first |
| Any mode + candidate count | `/ml-modeling-autoresearch <project> until plateau, 4 candidates` | Same as the mode chosen |

Default candidates per round is 2 (`program.md`'s `candidates_per_round`);
state a count in the request (as above) to override it, for every round the
invocation runs, without editing `program.md`.

Stopping is plateau-based (a streak of rounds with no real improvement), not
a guessed time or round count on its own — round duration scales with model
complexity and data size, so a fixed number means something different per
project. In a multi-round mode, hitting `patience` (default 5) or the round
ceiling now actually ends the session — the skill owns its own recurrence,
so there's nothing external left running to stop separately. It can only
ever write inside `modeling/autoresearch/` plus `04-evaluate.md`/`.json` —
never `prd/`, `adr/`, `design/`, or `spec/`.

Full detail: `.agents/skills/personal/ml-modeling-autoresearch/SKILL.md`,
`.agents/skills/personal/adr/0003-autoresearch.md`, and
`.agents/skills/personal/adr/0005-autoresearch-self-contained-looping.md`.

## Skill improvement log

Every skill in both families — `ml-system-design-*` and `ml-modeling-*` —
can log a proposed improvement to *itself*, not the project it's working on,
to `<project-folder>/SKILL-IMPROVEMENTS.md`. Two triggers:

| Source | What it means |
|---|---|
| Agent-found | A bug in the skill's own instructions, or a genuinely better way to do the step |
| User-requested | You ask to change how the skill behaves, not just this project's data/design |

Each entry is appended, never overwritten:

```markdown
## <date> — <skill-name>
- **Source**: agent-found bug | agent-found better design | user-requested
- **Status**: proposed
- **Finding**: <what's wrong or what could be better, concretely>
- **Suggested change**: <the actual edit, concrete enough to apply as-is>
```

Nothing is applied automatically — a `SKILL.md` is shared across every
future project, so a silent edit from one project's run would change
behavior for every other project without you ever deciding to. Instead: any
skill, at the end of a run, checks for entries still marked `proposed` and
offers to review them with you. Adopting one applies it as a real edit to
the skill file under `.agents/skills/personal/<skill>/SKILL.md`, then flips
that entry's `Status` to `adopted` or `declined` — entries are never
deleted, so the file stays a durable per-project record of what was
proposed and decided.

Full rationale (why per-project over centralized, why log-and-review over
auto-apply): `.agents/skills/personal/adr/0004-skill-improvement-log.md`.

## Command reference

Every skill supports an explicit `/skill-name` command — that's a Claude Code
universal, not something invocation mode changes. Two skills have no
natural-language trigger at all and *require* the command; the rest also
fire from plain conversation.

| Skill | Purpose | Command | Also triggers from plain language? |
|---|---|---|---|
| `ml-system-design` | Router — whole design doc | `/ml-system-design <topic>` | Yes |
| `ml-system-design-prd` | Grill Definition, write `prd/` | `/ml-system-design-prd <topic>` | No — command required |
| `ml-system-design-definition` | Definition section directly (draft/review, no grilling) | `/ml-system-design-definition` | Yes |
| `ml-system-design-high-level` | ML framing, architecture, phasing → `design/high-level.md` | `/ml-system-design-high-level` | Yes |
| `ml-system-design-deep-dive` | Data/features/models/training → `design/deep-dive.md` | `/ml-system-design-deep-dive` | Yes |
| `ml-system-design-delivery` | Rollout, eval, monitoring, fallback | `/ml-system-design-delivery` | Yes |
| `ml-system-design-post-delivery` | Analysis, explainability, iteration | `/ml-system-design-post-delivery` | Yes |
| `ml-modeling` | Router — data→features→train→evaluate | `/ml-modeling <topic>` | Yes |
| `ml-modeling-data` | Profile data → `modeling/01-data.md` | `/ml-modeling-data` | Yes |
| `ml-modeling-features` | Engineer features → `modeling/02-features.md` | `/ml-modeling-features` | Yes |
| `ml-modeling-train` | Train one model, sequential → `modeling/03-train.md` | `/ml-modeling-train` | Yes |
| `ml-modeling-multiagent` | Train N candidates, parallel → same slot | `/ml-modeling-multiagent` | Yes |
| `ml-modeling-evaluate` | Evaluate → `modeling/04-evaluate.md` | `/ml-modeling-evaluate` | Yes |
| `ml-modeling-autoresearch` | Optional: auto-improvement, 3 modes (see above) | `/ml-modeling-autoresearch <project> [mode]` | No — command required |
| `ml-system-design-monkey-mode` | Fast autonomous baseline, background | `/ml-system-design-monkey-mode <topic>` | No — command required |

## Project folder

Every topic gets one folder at the repo root, `ml-<topic-slug>-<n>/`:

```
ml-<topic>-<n>/
  prd/<topic>.md            Definition, from ml-system-design-prd
  adr/000N-*.md             Architecture decisions, any stage, one per file
  design/high-level.md      ML framing, architecture diagrams, phasing
  design/deep-dive.md       Data/features/models/training decisions
  spec/<topic>.md           Design→modeling fork synthesis; first line is
                             deep-dive-hash: (drift check, see below)
  dashboard/                eda.ipynb + app.py (Streamlit), EDA + Results
                             only, Regular/Quick-POC, never monkey-mode
    .port                    This project's Streamlit port (per-project,
                             so two dashboards never collide)
  modeling/                 01-data(.md/.json) → 02-features → 03-train →
                             04-evaluate(.md/.json), .json feeds dashboard
    experiments.json         experiment_tracker log, always via --log-file
    autoresearch/            Optional, after 04-evaluate.json exists, 3
                             self-contained modes, see above; has its own
                             experiments.json
  monkey-mode/              Independent fast-baseline track (report.md)
  SKILL-IMPROVEMENTS.md     Proposed fixes to the skills themselves, any
                             stage — logged, reviewed on request, see above
```

Regular vs. Quick-POC mode (keyword-selected: "poc"/"quick"/"mvp"/"fast" vs.
nothing) applies across the design path and `ml-modeling-*` — monkey-mode
has its own always-fast behavior and doesn't use this switch.

## Running things concurrently

The family is built so that runs which naturally overlap never write the
same files. No git worktree is needed for any of these; each row's isolation
is the folder split, not a checkout:

| Pattern | Writes | Shared with the other side |
|---|---|---|
| Design path + monkey-mode, one project | `design/`, `prd/`, `adr/` vs. `monkey-mode/` | `SKILL-IMPROVEMENTS.md` (append-only) |
| Design continues while a fork runs `ml-modeling-*` | `design/` vs. `modeling/`, `spec/`, `dashboard/` | `design/deep-dive.md` — read by every modeling step, so it can drift (see below) |
| You edit by hand while autoresearch loops | Yours: `program.md`, `modeling/01-03*`, `design/`. The loop's: `autoresearch/experiment.py`, `best_metrics.json`, `rounds/`, `04-evaluate.*` | Nothing, if you stay on your side of that line |
| Two projects at once (e.g. churn + ranking) | Two disjoint project folders | Only process/git state: the dashboard port and the git index |

Three mechanics keep the shared bits from colliding:

- **Per-project dashboard port.** `ml-modeling-data` picks the first free
  port from 8501 up, writes it to `dashboard/.port`, and launches Streamlit
  on it; `ml-modeling-evaluate` health-checks that port, never bare `:8501`.
- **Explicit experiment log.** Every `experiment_tracker.py` call passes
  `--log-file <project>/modeling/experiments.json` (autoresearch:
  `modeling/autoresearch/experiments.json`). The script's default is relative
  to the agent's CWD, which is wherever it happened to be.
- **Deep-dive drift: detect, then ask.** `spec/<topic>.md` starts with
  `deep-dive-hash:` (from `git hash-object -w design/deep-dive.md`). Each
  `ml-modeling-*` step recomputes the hash first; on a mismatch it shows the
  diff and asks two things before doing its work: re-synthesize the spec or
  keep it, and apply the changed decisions going forward or proceed on the
  old ones. The answer is recorded in that step's `.md`. Autoresearch never
  asks — it notes the change in `round-summary.md` and the next interactive
  step raises it.

One git rule for any agent in a shared working tree: never run `git stash`,
`checkout`, `restore`, `reset`, or `clean`. Those discard uncommitted files,
and in a shared tree some of them belong to another session.

**When a worktree does earn its keep**: two projects whose histories need
independent commits while both are mid-flight (separate branches, separate
index). Reach for Claude Code's `EnterWorktree`, or
`Agent(isolation: "worktree")` for a background run, on demand — no standing
setup. Know the costs before you do: `.venv` is gitignored, so `uv sync`
again; `data/`, `*.csv`, `*.pkl`, `models/` are gitignored, so an existing
project's data and trained models are absent in the new tree; Claude Code
keys permissions and memory by directory path, so prompts start fresh; and
anything uncommitted on `main` (a skill you're mid-way through editing) is
invisible there. Skill edits stay on `main` regardless.

## Where to go deeper

`.agents/skills/personal/adr/0001-ml-modeling-family-and-continuity.md` has
the full rationale, both complete usage-path tables, and the
mattpocock-integration decision (why this family doesn't call
`to-spec`/`implement`/`implement-spec`). `adr/0004-skill-improvement-log.md`
covers the skill improvement log above. This guide is the fast orientation;
those ADRs are the reference.
