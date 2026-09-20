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
/ml-system-design-prd  (whole design path)
  │
  ▼
-high-level  (offers an ADR on real tradeoffs)
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
| `ml-system-design-high-level` | ML framing, architecture, phasing | `/ml-system-design-high-level` | Yes |
| `ml-system-design-deep-dive` | Data/features/models/training → `design/deep-dive.md` | `/ml-system-design-deep-dive` | Yes |
| `ml-system-design-delivery` | Rollout, eval, monitoring, fallback | `/ml-system-design-delivery` | Yes |
| `ml-system-design-post-delivery` | Analysis, explainability, iteration | `/ml-system-design-post-delivery` | Yes |
| `ml-modeling` | Router — data→features→train→evaluate | `/ml-modeling <topic>` | Yes |
| `ml-modeling-data` | Profile data → `modeling/01-data.md` | `/ml-modeling-data` | Yes |
| `ml-modeling-features` | Engineer features → `modeling/02-features.md` | `/ml-modeling-features` | Yes |
| `ml-modeling-train` | Train one model, sequential → `modeling/03-train.md` | `/ml-modeling-train` | Yes |
| `ml-modeling-multiagent` | Train N candidates, parallel → same slot | `/ml-modeling-multiagent` | Yes |
| `ml-modeling-evaluate` | Evaluate → `modeling/04-evaluate.md` | `/ml-modeling-evaluate` | Yes |
| `ml-system-design-monkey-mode` | Fast autonomous baseline, background | `/ml-system-design-monkey-mode <topic>` | No — command required |

## Project folder

Every topic gets one folder at the repo root, `ml-<topic-slug>-<n>/`:

```
ml-<topic>-<n>/
  prd/<topic>.md       Definition, from ml-system-design-prd
  adr/000N-*.md        Architecture decisions, any stage
  design/deep-dive.md  Data/features/models/training decisions
  spec/<topic>.md      Design→modeling fork synthesis
  modeling/            01-data → 02-features → 03-train → 04-evaluate
  monkey-mode/         Independent fast-baseline track (report.md)
```

Regular vs. Quick-POC mode (keyword-selected: "poc"/"quick"/"mvp"/"fast" vs.
nothing) applies across the design path and `ml-modeling-*` — monkey-mode
has its own always-fast behavior and doesn't use this switch.

## Where to go deeper

`.agents/skills/personal/adr/0001-ml-modeling-family-and-continuity.md` has
the full rationale, both complete usage-path tables, and the
mattpocock-integration decision (why this family doesn't call
`to-spec`/`implement`/`implement-spec`). This guide is the fast orientation;
that ADR is the reference.
