# Skill improvements - ml-churn-1

## 2026-09-20 - ml-system-design (docs/ML-SKILLS-GUIDE.md)
- **Source**: user-requested
- **Status**: adopted (2026-09-20)
- **Applied to**: `docs/ML-SKILLS-GUIDE.md` (shape diagram root + first bullet), `.agents/skills/personal/README.md` (entry-point line). `notes/` template not touched (user's file).
- **Finding**: `docs/ML-SKILLS-GUIDE.md` names `/ml-system-design-prd` as the first step ("Start with PRD, then high-level") and its shape diagram starts at `topic -> prd`. The intended entry point is `/ml-system-design`: it is the skill that resolves Regular vs. Quick POC mode, offers the two hand-run questions (monkey-mode in parallel? PRD first?), and then invokes the five sections. A reader who starts at the PRD skips that gate; this run started from a notes file saying "use this as the input to ml-prd or monkey mode" for the same reason.
- **Suggested change**: In `docs/ML-SKILLS-GUIDE.md`, (1) add `/ml-system-design <topic> [poc]` as the root of the shape diagram above `topic`, with a note "entry point: picks the mode and offers the two commands below"; (2) rewrite the first "Three things to know" bullet to: "**Start with `/ml-system-design <topic>`.** It picks Regular vs. Quick POC from your wording, then asks two questions: run `/ml-system-design-monkey-mode` in parallel? scope with `/ml-system-design-prd` first? Both are hand-run commands; answer them, then come back to `/ml-system-design` for the five sections." (3) Mirror the same one-line pointer at the top of `.agents/skills/personal/README.md` ("Entry point: `/ml-system-design`"). Also update `notes/` templates that point at `ml-prd or monkey mode` directly.

## 2026-09-20 - ml-system-design-prd
- **Source**: user-requested
- **Status**: adopted (2026-09-20)
- **Applied to**: `ml-system-design-prd/SKILL.md` (Quick POC round shape + split sentence), `ml-system-design-definition/SKILL.md` (when-invoked-from-prd line), `docs/ML-SKILLS-GUIDE.md` (first bullet).
- **Finding**: In Quick POC mode `ml-system-design-prd` and `ml-system-design-definition` overlap almost completely: `-definition` POC says "state each item's most likely answer in one pass, flagged as an assumption" and `-prd` POC says "batch into fewer, larger rounds, accept the first reasonable answer". In practice the PRD's one POC round is exactly the `-definition` POC draft with a question mark on each item, but neither skill says so, which reads as two skills doing the same job. The split is real (checklist + drafting vs. interview + folder creation), just undocumented.
- **Suggested change**: In `ml-system-design-prd/SKILL.md`, after the Regular vs. Quick POC paragraph, add: "Quick POC round shape: produce `ml-system-design-definition`'s one-pass POC draft (every checklist item with its most likely answer) and present it as a single grilling round, each item a numbered question with the draft answer as the recommendation. The user's confirmations and overrides become the PRD; the draft is never written to `design/definition.md` by this skill." In `ml-system-design-definition/SKILL.md`, add one line under the Quick POC sentence: "When invoked from `ml-system-design-prd`, the one-pass draft is shown as a grilling round, not written to `design/` - see that skill." And in `docs/ML-SKILLS-GUIDE.md`, one sentence explaining the split: "`-prd` is the interview (hand-run, creates the folder, writes `prd/`); `-definition` is the checklist and the drafted section (`design/definition.md`), and `-prd` reuses its checklist rather than keeping a copy."

## 2026-09-20 - ml-system-design
- **Source**: agent-found bug
- **Status**: adopted (2026-09-20)
- **Applied to**: `ml-system-design/SKILL.md` (PRD-is-definition rule after the numbered list; fork line now `prd (= definition)`).
- **Finding**: `ml-system-design/SKILL.md` opens with "Five sections ... invoked in order for a full doc: 1. `-definition` ...", but the fork diagram in the same file and the guide's shape diagram both go `prd -> high-level -> ...` with no `-definition` step. When `prd/<topic>.md` exists, the PRD already is the resolved Definition checklist; running `-definition` after it would only paraphrase the PRD into `design/definition.md`. The agent followed the literal "in order" text and told the user the next step after the PRD was `-definition`.
- **Suggested change**: In `ml-system-design/SKILL.md`, after the numbered list, add: "If `<project-folder>/prd/<topic>.md` exists, it is the Definition section - do not run `-definition` to draft it again; start the full doc at `-high-level`. `-definition` is invoked directly only for a project without a PRD, or to review an existing Definition section." Rename the fork line's leading node from `prd` to `prd (= definition)` so the two diagrams agree.

## 2026-09-20 - ml-system-design (all sections) + ml-modeling (all steps)
- **Source**: user-requested
- **Status**: adopted (2026-09-20)
- **Applied to**: `ml-system-design/SKILL.md` ("Hand edits between steps"), `ml-modeling/SKILL.md` (paragraph after the autoresearch note), `docs/ML-SKILLS-GUIDE.md` (bullet).
- **Finding**: The user can hand-edit any intermediate document (PRD, high-level, ADR, spec, modeling step) and tell Claude, expecting the downstream steps to be re-run. The hands-on route already does this via the spec hash check for `prd/` and `design/high-level.md`; the design route and the modeling step files had no stated rule, and the guide never told the user this is allowed.
- **Suggested change**: Add a "Hand edits between steps" section to `ml-system-design/SKILL.md` (re-read, re-run downstream in the stated order, one `## Change log` line per touched file), a pointer to it from `ml-modeling/SKILL.md` under "Design docs changed?" covering `modeling/0N-*.md`, and a user-facing bullet in `docs/ML-SKILLS-GUIDE.md`.

## 2026-09-20 - ml-system-design-high-level, then every skill that writes a doc
- **Source**: user-requested
- **Status**: adopted (2026-09-20)
- **Applied to**: `ml-system-design/SKILL.md` ("Output docs"), `ml-modeling/SKILL.md` ("Output docs" pointer), the Project-folder line in `-definition`, `-high-level`, `-deep-dive`, `-delivery`, `-post-delivery`, `ml-modeling-data/-features/-train/-multiagent/-evaluate`, the write line in `-prd` and `-monkey-mode`, `docs/ML-SKILLS-GUIDE.md` (bullet).
- **Finding**: `design/high-level.md` was written with a five-column table whose cells ran to several hundred characters, and framing-table rows of similar length; unreadable in a terminal. The same risk applies to every skill that writes under the project folder.
- **Suggested change**: One "Output docs" rule in `ml-system-design/SKILL.md` (prose wrapped at 80 columns, code blocks exempt, a table wider than 80 columns becomes headed paragraphs), mirrored as a pointer in `ml-modeling/SKILL.md`, and referenced from the "Project folder" line of every section and step skill plus `-prd` and `-monkey-mode`. Guide gets a one-line bullet.
