# One shared skill improvement log; reflect at the end of every session

## Context

ADR 0004 set up the skill improvement log: each skill logs a proposed
change to itself in `<project-folder>/SKILL-IMPROVEMENTS.md`, and offers a
review at the end of each run. On 2026-10-09 (project
`labs/ml-riot-wiki-recommender-1`) the user pointed out 2 gaps:

- The trigger lived inside each skill run. Issues found between runs (in
  discussion, user corrections, follow-up work) were logged only when the
  user asked: 11 entries came from one session-end reflection the user
  requested, none from the per-run step.
- The log sat in the project folder, so it read as "improvements for this
  project". The user wants it to serve the skills and future projects.
  There was no view across projects (kkbox 0, riot-churn 0, riot-wiki 11
  proposed).

## Decision

1. **One shared log:** `.agents/skills/personal/SKILL-IMPROVEMENTS.md`.
   Each entry adds a `Project` line. The per-project files stay as
   history; their open entries moved to the shared log.
2. **Session-end reflection:** at the end of every session that used an
   `ml-*` or `ml-critique*` skill, before the final summary, the agent
   reflects on the whole session, logs new skill issues, and offers a
   review of the `proposed` entries. The rule is in the sandbox
   `CLAUDE.md` (always loaded) and in `ml-system-design/SKILL.md`, "Skill
   improvement log" (the single source of truth for the skills).
3. **User corrections are logged at once**, not at session end.
4. Unchanged from ADR 0004: log, then review; never apply silently;
   never delete an entry.

## Consequences

- A session that ends early still gets its issues logged, if the agent
  reaches the summary. A crash or a hard stop still loses them.
- One review covers all projects. Entries keep their project name, so
  the evidence is still traceable.
- The per-run "Reflect" step in "Check the output" stays: it catches
  issues while the details are fresh.
