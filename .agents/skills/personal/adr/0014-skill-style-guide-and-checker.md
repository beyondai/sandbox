# A written style guide, 2 checkers, and a rule to run them

## Context

ADR 0011 applied 9 skill-writing guides to the `ml-*` skills. The rules
lived only in that ADR and in a user note. Nothing checked them after the
rewrite. On 2026-10-09 the user asked for 3 things:

1. Write the style rules down in `docs/`.
2. Run the style checks after this change and after each major skill
   change.
3. Later the same day: add a permanent step that updates and checks the
   files in `docs/` for style and for consistency with the skills. The
   first checks covered only the skill files.

## Decision

```
docs/SKILL-STYLE-GUIDE.md      the rules (for people, STE)
        |
        +-- skills: check_skill_style.py + skills checklist  (steps 1-2)
        +-- docs:   update, check_docs.py + docs checklist    (steps 3-5)
        |
CLAUDE.md "Skill and docs      when: steps 3-5 after every skill change
 changes"                            and docs edit; 1-2 after a major one
```

1. **The guide** (`docs/SKILL-STYLE-GUIDE.md`): the 2 audiences (skill
   files in plain English, outputs in STE), the 9 structure rules with
   their reasons, the shared references, how to check, and when.
2. **The checker** (`.agents/skills/personal/scripts/check_skill_style.py`,
   stdlib): frontmatter name and description, `SKILL.md` at most 500
   lines, Contents over 100 lines, no em dash, a Check heading, paths that
   resolve, every `references/` and `scripts/` file named in `SKILL.md`,
   and a `Requires:` line in each script. It is separate from
   `check_doc.py` because skill files have other rules (no 80-column
   limit).
3. **The docs checker** (`.agents/skills/personal/scripts/check_docs.py`,
   stdlib): the `check_doc.py` rules on each `.md` in `docs/`, 80 columns
   and em dashes on `.txt`, Contents over 100 lines, anchors and paths
   that resolve. For consistency: each skill is named in `docs/`, each
   cited ADR exists, and each ADR has a README index row. A docs
   checklist covers counts, diagrams, keywords, and the template.
4. **The rule** (sandbox `CLAUDE.md`, "Skill and docs changes"):
   - after every skill change, major or not: update the docs, then run
     the docs steps. Reason: a small change makes the docs wrong as
     easily as a big one;
   - after every docs edit: the docs steps;
   - after a major skill change (a new skill, a rewrite, 3 or more skill
     files, or a new shared reference): also the skills steps, and an
     ADR.

## Consequences

- The checker skips `adr/` (historical records, some with em dashes),
  `tests/`, and `assets/`.
- Paths into a project folder (`../modeling/...` in the dashboard text)
  are not skill paths. The checker skips the project subfolder names.
- The first run found 1 gap: `hypothesis_tester.py` had no `Requires:`
  line. It was added.
- The checkers cannot judge freedom level, reasons, plain English, or if
  a doc describes the skills correctly. The 2 checklists cover them.
- A test with 5 planted errors in a copy of `docs/` (a broken anchor, a
  broken path, an em dash in the template, a skill missing from the
  docs, a cited ADR that does not exist) gave 5 failures.
