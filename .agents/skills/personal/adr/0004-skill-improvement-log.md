# Skill improvement log: per-project, log-and-review, whole-family

Both `ml-system-design-*` and `ml-modeling-*` now log potential improvements to *the skills themselves* — not the project they're working on — to `<project-folder>/SKILL-IMPROVEMENTS.md`, triggered either by the agent noticing a bug or a better design mid-run, or by the user asking for a change to how a skill behaves. Entries are reviewed by the user later, on request, and only then applied as a real edit to the relevant `SKILL.md`.

## Decisions

**Per-project file (`SKILL-IMPROVEMENTS.md`), not a centralized one per skill.** Matches the file-based-handoff convention this whole family already runs on — every other artifact (`design/deep-dive.md`, `modeling/03-train.md`, `monkey-mode/report.md`) lives under the project folder, not scattered into the skill directories themselves. A proposed change sits next to everything else about the project that surfaced it, so reviewing it later has the same context a fresh session would need to re-derive why it was suggested.

**Log-and-review, never auto-apply.** A `SKILL.md` is shared across every future project that invokes it — a change one project's run silently applied would change behavior for every other project without the human ever deciding to. Logging only, with an explicit adopt/decline step per entry, keeps the skill files themselves stable mid-run and puts the actual editing decision where it belongs: with the person who owns this skill set, reviewing a batch rather than drive-by edits happening underneath them.

**Whole-family scope (`ml-system-design-*` and `ml-modeling-*`), not `ml-modeling-*` alone.** The user asked for this on "my personal ml-related skill set," not one sub-family. Confirmed explicitly when asked: apply uniformly to both families rather than leaving one half of the pipeline silently exempt, which would be a surprising inconsistency for whichever family didn't get it.

**Entries are never deleted, only status-flipped (`proposed` → `adopted`/`declined`).** The file is a durable per-project record of what was proposed and decided, not a queue that gets emptied — useful the same way `adr/` and experiment logs elsewhere in this family are: a record of *why*, not just current state.

## Considered Options

Considered a centralized `IMPROVEMENTS.md` per skill directory (e.g. `.agents/skills/personal/ml-modeling-data/IMPROVEMENTS.md`), accumulating across every project that ever used that skill. Rejected: breaks the family's existing rule that nothing meaningful lives outside a project folder except the skills themselves — the skill directories are meant to hold only the skill's own instructions and bundled tools, not a growing log written by whichever project last ran it. A per-project file also keeps review scoped and reviewable in one sitting, rather than an ever-growing cross-project backlog with no natural checkpoint.

Considered auto-applying an agent-found bug fix immediately (skip logging, just fix the `SKILL.md` inline) on the theory that an obvious bug shouldn't need a review step. Rejected: "obvious" is exactly the kind of judgment call that's cheap to get wrong under time pressure mid-task, and a skill file changing itself with no human checkpoint is a different risk profile than logging a proposal — even a correct fix silently changing shared, cross-project behavior isn't something this family does anywhere else.

## Consequences

- Every project folder can now grow a `SKILL-IMPROVEMENTS.md` at its root, alongside `prd/`, `adr/`, `design/`, `spec/`, `modeling/`, `dashboard/`, `monkey-mode/` — reflected in `docs/ML-SKILLS-GUIDE.md`'s project-folder layout diagram.
- A user working across many practice projects will end up with the same proposed skill change logged independently in several projects' `SKILL-IMPROVEMENTS.md` files if it keeps recurring — there's no cross-project dedup. If that turns out to be noisy in practice, revisit the per-project-vs-centralized decision above rather than bolting dedup onto the per-project design.
- Reviewing and adopting an entry is a manual, skill-file edit each time — there's no batch-apply-all mechanism. Consistent with the log-and-review decision above: adoption is deliberate per entry, not a bulk operation.
