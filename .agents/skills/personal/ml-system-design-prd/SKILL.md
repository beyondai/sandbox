---
name: ml-system-design-prd
description: >-
  Grill the user on the Definition checklist (problem, requirements, metrics,
  team) for a specific ML system design topic, then write the resolved answers
  into a PRD. Run by hand only, e.g. /ml-system-design-prd design ecommerce
  product search.
disable-model-invocation: true
---

# ML System Design PRD

Call the Skill tool twice: `ml-system-design-definition` for the checklist,
`grilling` for the interview mechanics.

Seed `grilling`'s design tree from the Definition checklist bullets — Problem,
Requirements (scope, non-functional), Metrics (offline, online), Team
(stakeholders, reuse) — each scoped to the topic in `$ARGUMENTS`. Every bullet
is a branch; run the rounds until the frontier is empty, same as `grilling`
always does. Don't skip Requirements — scope's out-of-scope list or the
offline/online metric split just because the topic feels obvious — grilling
exists precisely to stop those from being silently assumed.

## Answers can arrive in a notes file

The user may answer a round by pointing at a notes file (`@notes/<topic>.md`)
instead of typing in chat, and will mix the two: long answers in the file,
short ones inline. The file is one long-lived document per session with the
user's own section labels (e.g. `#to-prd`), not a fixed schema. When a round's
answer is such a reference: read the file, match its content to the open
questions by the user's labels, and treat only content added since the last
time this session read the file as new input - never re-process the whole
file. Say which questions the new content answered and which are still open.

Regular vs. Quick POC (keyword-selected, see
`../adr/0001-ml-modeling-family-and-continuity.md`) changes the grill's pace,
not its coverage: Quick POC still touches every bullet, but batches them into
fewer, larger rounds and accepts the first reasonable answer instead of pushing
for precision — grilling's exhaustiveness is the one thing POC mode doesn't get
to skip here, since a PRD missing a branch entirely defeats the point of using
this skill at all.

Each topic gets its own project folder, `labs/ml-<topic-slug>-<n>/` (e.g.
`labs/ml-ecommerce-search-1/`) — every design artifact for that project (PRD,
ADRs, later design-doc sections) lives under it, so a repo with multiple
practice projects stays sorted by project rather than by doc type. Before
writing, check for existing `ml-<topic-slug>-*` folders: if none exist, use
`-1`; if some exist, ask the user whether this continues an existing one or
starts a new numbered attempt at the same topic.

When the frontier empties, write the settled answers to
`<project-folder>/prd/<topic-slug>.md`, one heading per checklist bullet, in the
user's own words and numbers — never the placeholder-style assumptions a draft
pass would use. Confirm the slug with the user if the topic name is ambiguous.

Done when the PRD file exists and every checklist bullet has a concrete,
user-confirmed answer under its heading.

If this run turns up a bug or a better design in this skill, or you ask for a
change to how it works, log it — see `../ml-system-design/SKILL.md`'s Skill
improvement log.
