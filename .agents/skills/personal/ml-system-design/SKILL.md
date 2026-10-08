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

For a full doc, invoke each in order. If `<project-folder>/prd/<topic>.md`
exists, it is the Definition section: start the full doc at
`ml-system-design-high-level`, and reserve `ml-system-design-definition` for a
project without a PRD or for reviewing an existing Definition section. For a
single-section ask, invoke that skill directly and skip this one next time. For interview prep, narrate through
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

Monkey-mode runs concurrently with PRD/design work on the same project
folder by design (see the track below) — when dispatching it, describe the
project folder as shared, in-progress state, not an empty one to set up from
scratch, even on a brand-new project. A background agent told a shared path
"does not exist yet" has previously reset the whole folder instead of only
creating its own `monkey-mode/` subdirectory, destroying a PRD the foreground
session had just written.

Every artifact for a project lives in its project folder (see "Project
folder" below), not scattered into repo-wide `docs/` or `notes/`. Write ADRs for a project's architectural
decisions into `<project-folder>/adr/`, following the numbering and
when-to-write rules in the `domain-modeling` skill's ADR format — only the
location is project-scoped, the format itself is unchanged. ADRs stay
one-per-decision even as a project accumulates several - never a single running
project-decisions log, and never the home for a whole design section (each
section has its own file under `design/`).

## Project folder

This section is the single source of truth for where all `ml-*` and
`ml-critique*` skills save local docs and designs.

```
<parent>/                  default: labs/ (the user can name another)
  <project>/               for example: proj1/
    prd/  design/  adr/  spec/  modeling/  dashboard/
    critique/  research/  monkey-mode/  monkey-mlp/
```

- **Project name.** Use the name that the user gives (for example
  `proj1`), as a lowercase slug. If the user gives only a topic, propose
  `ml-<topic-slug>` and confirm it. Add `-<n>` only for a new attempt at a
  project that already exists: ask "continue the existing project, or
  start a new attempt?" first.
- **Parent folder.** The default is `labs/`. The user can name another
  parent in the request (for example "put proj1 in ~/work/designs"). Use
  that parent for the project. Later requests name the project by its path.
- **Subfolders.** A skill creates its subfolder the first time that it
  writes there. Every other file generated for the project (research,
  notes for the project, test records) goes in a subfolder of the project
  folder. Never in `notes/`: it holds only what the user typed or pasted.

### Which project folder

Use the first rule that applies:
1. The project named in the request. A path is used as given. A name with
   no path is looked up under `labs/`.
2. The project folder that this conversation already read or wrote.
3. If exactly one project folder exists under `labs/`, that one. A
   project folder is a direct child of the parent that has at least one of
   the subfolders above.
4. Ask the user.

Only `/ml-system-design-prd` and the monkey tracks create a new project
folder. Section and step skills never create one.

## Output docs

Every file that a skill in this family creates goes in the project folder.
`notes/` holds only content that the user typed or pasted: read it, but do
not create files there.

Every file written under the project folder (`prd/`, `design/`, `adr/`,
`spec/`, `modeling/`, `monkey-mode/`, `critique/`) wraps prose at 80
columns: hard line breaks inside paragraphs and list items, continuation
lines indented under their bullet. Fenced code blocks are the exception. A
table whose row would run past 80 columns becomes a list of headed
paragraphs instead - the reader is a human in a terminal, not a renderer.

Write the prose in approximately 80% of ASD-STE100: short sentences (20
words or fewer for instructions, 25 for descriptions), one instruction in
each sentence, active voice, one word for one meaning, and lists instead of
long paragraphs. Keep technical names as they are. Add an ASCII diagram
(fenced) next to the text when structure, data flow, sequence, or a timeline
is easier to see than to read. The diagram is an addition: the text stays
complete without it.

## Hand edits between steps

Every file under the project folder is the user's to edit by hand between
steps. When the user says a file changed, or a re-read shows it did: re-read
it, then re-run each downstream step whose file cites the changed content,
updating those files in place. Downstream order: `prd/` feeds
`design/high-level.md`, which feeds `design/deep-dive.md` or `spec/` +
`modeling/`, which feed `delivery` and `post-delivery`. Each touched file
gets one line under a `## Change log` heading at its end saying what moved
and why. On the hands-on route the hash check in `../ml-modeling/SKILL.md`,
"Design docs changed?", catches the same edits without being told.

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
prd (= definition) -> high-level -> [ -deep-dive (paper) | ml-modeling-* (hands-on) ] -> -delivery -> -post-delivery
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

## Design principles

`../ml-design-principles.md` holds the principles that every section and
step skill applies, and that `ml-critique` reviews against. Principle 1:
simple by default, complex only with evidence.

## Critique a finished write-up: `ml-critique`

The Review mode of each section skill examines coverage. To judge the
quality of the decisions in a finished design, and to settle each finding
with the user, use `ml-critique`. It writes `<project-folder>/critique/`.

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
