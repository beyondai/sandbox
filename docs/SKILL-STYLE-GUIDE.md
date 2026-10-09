# Skill Style Guide

## Contents

- [Scope](#scope)
- [Writing rules](#writing-rules)
- [The 9 structure rules](#the-9-structure-rules)
- [Shared references](#shared-references)
- [Evals](#evals)
- [How to check](#how-to-check)
- [When to check](#when-to-check)

## Scope

This guide gives the style rules for 2 kinds of files, and how to check
them:
- the skills in `.agents/skills/personal/`;
- the docs in `docs/`, which describe the skills to people.
- The rules come from 9 guides for skill files
  (`notes/skill-improve-guides-20261008.md`).
- ADR 0011 records how the `ml-*` skills applied them
  (`.agents/skills/personal/adr/0011-skill-writing-guides.md`).
- ADR 0014 records this guide and its checker.
- ADR 0015 records what the Anthropic skill checklist added: evals,
  named constants, and 3 more checks.

## Writing rules

There are 2 audiences. Each audience has its own rules.

```
skill files (an agent reads them)    outputs (a person reads them)
SKILL.md, references, shared .md     docs/, design docs, reports, chat
---------------------------------    ---------------------------------
concise plain English                about 80% ASD-STE100
imperative steps, lists              short sentences, active voice
one term for one concept             one word for one meaning
a one-line reason for each rule      lists over long paragraphs
that is not obvious                  80-column wrap (code blocks exempt)
no em dashes                         no em dashes
                                     a diagram next to the text when
                                     structure or flow is easier to see
```

- **Skill files do not use strict STE.** Strict STE removes the reasons.
  A strong model needs the reasons to handle edge cases.
- **Keep technical names as they are.** Examples: file names, skill
  names, metric names.
- **Put long history in an ADR.** A skill file says what to do now.

## The 9 structure rules

1. **Contents for a file over 100 lines.**
   - Put a "Contents" line or section in the first 20 lines.
   - Reason: an agent often reads only the first 100 lines to decide if a
     file is relevant.
2. **Match the freedom to the risk of the task.**
   - High freedom: open guidance for creative or variable work (drafting
     a design section).
   - Medium freedom: a template with parameters (a report format).
   - Low freedom: a fixed script for a fragile or high-risk step.
3. **Use a script for a fragile step.**
   - Examples: `check_doc.py`, `spec_hash_check.sh`,
     `launch_dashboard.sh`.
   - Reason: a script gives the same result each time, and its code uses
     no context when it runs.
4. **Write for the target model.**
   - The skills are tuned for Claude Opus 5.5. Remove micromanagement that
     a strong model does not need.
   - The evals run on Opus only. Reason: a smaller model needs the
     micromanagement that this rule removes. This rule wins over the
     Anthropic checklist item "test with Haiku, Sonnet, and Opus".
   - Record the target model in `docs/ML-SKILLS-GUIDE.md`. Do not use a
     `model:` field in the frontmatter. Reason: in Claude Code, that field
     changes the model that runs the skill.
5. **Keep `SKILL.md` lean.**
   - The limit is 500 lines. Put detail in a reference file.
   - `SKILL.md` is the entry point and the index.
6. **Keep links 1 level deep.**
   - `SKILL.md` links each reference file directly.
   - A reference file does not send the reader to a third file for a
     required rule.
   - Reason: an agent often previews a nested file only in part.
7. **Use a Progress block when the order is important.**
   - The agent copies the checklist into its reply and ticks each line.
8. **End each skill with a Check step.**
   1. Intent: 2-6 yes/no questions for that skill.
   2. Format: `check_doc.py` on each `.md` output.
   3. Fix: fix and check again, at most 2 times.
   4. Reflect: write each skill gap to the shared
      `.agents/skills/personal/SKILL-IMPROVEMENTS.md`.
9. **Declare the dependencies.**
   - Each script has a `Requires:` line.
   - Each number in a script that is not obvious is a named constant
     with a one-line reason. Reason: a number with no reason is
     guesswork for the next reader.
   - `ml-modeling/SKILL.md`, "Bundled tools", lists each script and what
     it needs. Give the install command, for example `uv add <pkg>`.

## Shared references

Some facts are necessary in many skills. Put them in 1 shared file at the
top of `.agents/skills/personal/`. Each skill links that file directly.
- `ml-design-principles.md`: the complexity gate.
- `ml-model-training.md`: negatives, architecture, training setup.
- `ml-serving.md`: serving mode, latency, scaling, cost.
- `ml-playbooks.md`: the playbooks for each problem type.

Reason: 1 file for each fact. A change goes to 1 place, and the skills
stay the same.

## Evals

Each skill family has at least 3 evals in 1 test file.

```
family     test file                        tests
design     ml-system-design/tests/<date>    D1-D3
modeling   ml-modeling/tests/<date>         M1-M3
critique   ml-critique/tests/<date>         T1-T4, T5-T8
```

- Each test has an input, an answer key, and pass criteria.
- Use a real project from `labs/`. Run on a scratch copy.
- Run in a new session. The session that wrote the skill knows too much.
- Write the results in the test file. Fix the skills, then record the
  fixes.
- Run the evals again after a major skill change, and after a change of
  the target model.

## How to check

Steps 1-2 check the skills. Steps 3-5 update and check the docs.

**Step 1: run the script.** From the sandbox root:

```
python3 .agents/skills/personal/scripts/check_skill_style.py .agents/skills/personal
```

It prints `OK (<n> files)`, or `file:line: reason` for each failure. It
checks these rules:
- `SKILL.md` frontmatter: `name` is the folder name, and `description`
  exists.
- `description` has 1024 characters or fewer, and is in the third
  person (no "you", "your", "I", "me", "my").
- `SKILL.md` has 500 lines or fewer.
- A file over 100 lines has Contents in its first 20 lines.
- No em dash.
- Each `SKILL.md` has a Check heading.
- Each skill path resolves (links, and backtick paths that start with
  `../`, `references/`, `scripts/`, or `.agents/`).
- `SKILL.md` names each file in its `references/` and `scripts/`.
- Each script has a `Requires:` line.
- No backslash path (for example `scripts\run.py`). Use forward slashes.

The script skips `adr/` (historical records), `tests/`, and `assets/`.

**Step 2: do the manual checklist.** A script cannot judge these rules.
For each changed skill file:
- [ ] Is the freedom correct for the risk of each step (rule 2)?
- [ ] Does each rule that is not obvious have a one-line reason?
- [ ] Is it plain English, with imperative steps and lists?
- [ ] Is each concept always named with the same term? Do the other
      skills use the same term?
- [ ] Does each list of items (sections, steps, chain steps) agree with
      the other skills and with `docs/`?
- [ ] Does each fragile step use a script (rule 3)?
- [ ] Does each number in a script have a name and a reason (rule 9)?
- [ ] When 2 skills can do the same step (for example `ml-modeling-train`
      and `ml-modeling-multiagent`), do both write the files that the
      next steps load? Check each alternative, not only the default.

**Step 3: update the docs.** A skill change can make `docs/` wrong. Find
each doc that describes the changed skill (search `docs/` for its full
name and its short form, for example `mm-serve`). Update it in the same
change. Do not wait for a later cleanup.

**Step 4: run the docs script.** From the sandbox root:

```
python3 .agents/skills/personal/scripts/check_docs.py
```

It prints `OK (<n> files)`, or `file:line: reason` for each failure. It
checks these rules:
- Style, for each `.md` and `.txt` file in `docs/`:
  - the `check_doc.py` rules (80 columns, wide tables, em dashes, code
    fences);
  - Contents in the first 20 lines of a file over 100 lines;
  - each `#anchor` link matches a heading;
  - each link, and each path that starts with `.agents/` or `docs/`,
    resolves.
- Consistency with the skills:
  - each skill is named in `docs/` (full name or short form);
  - each ADR number that a doc cites exists;
  - each ADR has a row in the README index.

**Step 5: do the docs checklist.** A script cannot judge these rules.
For each doc that describes a changed skill:
- [ ] Is the text in about 80% STE: short sentences, active voice, lists?
- [ ] Do the counts agree with the skills (sections, items, chain steps,
      intent questions)?
- [ ] Do the flow diagram, the project tree, the command table, and the
      script list show the current skills and files?
- [ ] Do the keywords and commands match the skills (for example
      "parallel", "full chain", "poc")?
- [ ] Does the template (`docs/ml-design-template.txt`) have each item
      that the design skills require?
- [ ] Does the "Key design decisions" list name each new ADR?

## When to check

```
any skill change ──> steps 3-5 (docs)          always
major skill change ─> steps 1-2 (skills) + 3-5  always
docs edit only ────> steps 4-5                  always
```

- **Steps 1-2 (skills):** after each major skill change.
- **Steps 3-5 (docs):** after each skill change, major or not, and after
  each edit to a file in `docs/`. Reason: a small skill change (a new
  keyword, a renamed file) makes the docs wrong as easily as a big one.
- Run the steps before you say that the work is done. Show the output.

A major skill change is one of these:
- a new skill;
- a rewrite of a skill;
- a change to 3 or more skill files;
- a new shared reference.

The sandbox `CLAUDE.md` gives these rules to the agents.
