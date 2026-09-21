---
name: ml-system-design
description: >-
  Use when writing, structuring, or reviewing a full ML system design document,
  RFC, or ML system design interview answer for a machine learning product or
  feature (ranking, recommendation, search, fraud/risk, forecasting, NLP/LLM
  systems, etc). Entry point for the whole doc; for one section only, trigger
  that section's own skill directly instead. Trigger on "ML system design,"
  "design doc for a model," "ML RFC," or ML system design interview prep.
---

# ML System Design

Five sections, each its own skill, invoked in order for a full doc:

1. `ml-system-design-definition` — problem, requirements, metrics, team.
2. `ml-system-design-high-level` — ML framing, architecture, phasing.
3. `ml-system-design-deep-dive` — data, features, models, training.
4. `ml-system-design-delivery` — execution, deployment, eval, monitoring,
   fallback.
5. `ml-system-design-post-delivery` — analysis, explainability, iteration,
   democratize.

For a full doc, invoke each in order. For a single-section ask, invoke that
skill directly and skip this one next time. For interview prep, narrate through
the five in order, using each skill's bullets as the follow-ups an interviewer
would ask.

Scale depth to system size: a small internal model doesn't need
10M-req/min-grade detail in every subsection. The two subsections most often
skipped and most often flagged in review are out-of-scope
(`ml-system-design-definition`) and fallback (`ml-system-design-delivery`) —
never skip those two regardless of doc size.

Starting a new project: before invoking any section skill, ask two things in
one message - (a) run `/ml-system-design-monkey-mode <topic>` in parallel as a
background baseline? (b) scope with `/ml-system-design-prd <topic>` first? Both
are hand-run commands, so the user has to type them; your job is to make sure
they're offered rather than discovered later. Default recommendation: yes to
both. Only skip the questions when the user names a specific section to work
on. `/ml-system-design-prd` grills the user round-by-round on the Definition
checklist and writes the resolved answers into a project folder before any
drafting starts.

Each practice project is one folder under `labs/`, `labs/ml-<topic-slug>-<n>/`
(e.g. `labs/ml-ecommerce-search-1/`) — every artifact for that project (PRD, ADRs,
design-doc sections from the five skills above) lives under it, not scattered
into repo-wide `docs/`. Write ADRs for a project's architectural decisions into
`<project-folder>/adr/`, following the numbering and when-to-write rules in the
`domain-modeling` skill's ADR format — only the location is project-scoped, the
format itself is unchanged. ADRs stay one-per-decision even as a project
accumulates several - never a single running project-decisions log, and never
the home for a whole design section (each section has its own file under
`design/`).

## Regular vs. Quick-POC mode

Every section above supports both. Regular: full rigor, ask when unknown. Quick
POC: a one-hour MVP, not lower quality — `ml-system-design-deep-dive` in
particular answers all four of its items in one batched pass instead of asking
round by round. Mode is chosen by keyword in the request
("poc"/"quick"/"mvp"/"prototype"/"fast"/"one hour" → Quick POC;
"regular"/"full"/nothing → Regular), not a flag — this skill family has no
structured argument syntax. Full detail in
`adr/0001-ml-modeling-family-and-continuity.md`.

## Forking into execution: the `ml-modeling` family

`ml-system-design-*` stops at decisions on paper. `ml-modeling` (a separate
skill family: data → features → train → evaluate) is the hands-on version of
the deep dive. The fork sits right after `design/high-level.md`:

```
prd -> high-level -> [ -deep-dive (paper) | ml-modeling-* (hands-on) ] -> -delivery -> -post-delivery
```

Pick one. Both answer the same questions (data, features, models, training);
the paper one writes `design/deep-dive.md`, the hands-on one writes
`modeling/01`-`04` and does not read `design/deep-dive.md`. `-delivery` cites
whichever exists (real `04-evaluate.md` numbers when modeling ran). The first
`ml-modeling-*` call synthesizes `spec/<topic>.md` from PRD + ADRs +
high-level and pins their hashes; execution that contradicts the framing is
flagged back to `design/high-level.md`, not silently absorbed. See
`ml-modeling` for the chain, `adr/0006-fork-after-high-level.md` for why the
fork moved here, and `adr/0001-ml-modeling-family-and-continuity.md` for the
family's origin.

## A third, independent track: `ml-system-design-monkey-mode`

Not a step in either path above — a fully autonomous fast-baseline track that
shares only the project-folder root, nothing else (no `design/` or `prd/`
dependency, no `modeling/` writes). Run it by hand,
`/ml-system-design-monkey-mode <topic>`, alongside either path when you want a
real runnable baseline in the background while you keep working on the actual
design.

## Skill improvement log

Any `ml-system-design-*` skill, while it runs, may turn up something about the
*skill itself* worth fixing — not the design doc it's writing. Two triggers:

1. **Agent-found**: a bug in this skill's own instructions, or a genuinely
   better way to do the section than what's written.
2. **User-requested**: you ask to change how the skill behaves — as opposed to a
   one-off request specific to this project's design.

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
and decided. Same convention on the `ml-modeling-*` side; full rationale in
`adr/0004-skill-improvement-log.md`.
