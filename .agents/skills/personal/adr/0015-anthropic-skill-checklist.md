# The Anthropic skill checklist: evals, named constants, more checks

## Context

On 2026-10-09 the user gave the Anthropic "Checklist for effective
Skills" (22 items in 3 groups) and asked 2 things: which items improve
the `ml-*` skills, and which items conflict with the current style.

The audit found most items already met (ADR 0011, ADR 0014). It found 4
gaps and 1 conflict.

```
Checklist group     Met   Gap   Conflict
Core quality (10)    9     1       0
Code/scripts (8)     7     1       0
Testing (4)          1     2       1
```

## Decision

1. **Evals for each skill family.** At least 3 evals for each family, in
   `<entry skill>/tests/<date>-skill-test.md`. Format: setup, tests with
   an input, an answer key, and pass criteria, then results. Families:
   - design: `ml-system-design/tests/` (D1-D3, new);
   - modeling: `ml-modeling/tests/` (M1-M3, new);
   - critique: `ml-critique/tests/` (T1-T4, already there).
   A family, not each skill, because the skills in a family share the
   rules and pass files to each other. One test covers 2 or more skills.
2. **Named constants with a reason.** `feature_selector.py` and
   `bench_serve.py` had unexplained numbers (thresholds, weights,
   defaults). Each is now a named constant with a one-line reason. The
   output did not change.
3. **Descriptions in third person.** The 2 monkey skills said "you". The
   description goes into the system prompt, so a second speaker there
   makes triggering less reliable.
4. **3 more mechanical checks** in `check_skill_style.py`: description at
   most 1024 characters (the hard limit), description in third person,
   no backslash path. The checker now reads the full folded description.
   Before, it read only the first line.

**Conflict, kept as is:** "Tested with Haiku, Sonnet, and Opus". Rule 4
of the style guide tunes the skills for Claude Opus 5.5 and removes
micromanagement. A smaller model needs that micromanagement. To pass on
all 3 models, the skills must get longer and stricter for the strongest
one. The evals run on Claude Opus 5.5 only. Rule 4 now says so.

**Soft conflict, no change:** "No time-sensitive information".
`docs/ML-SKILLS-GUIDE.md` names the target model. That is a doc for
people, not a skill file, so the item does not apply.

## Consequences

- The new evals are written but not run. The first run of each family
  goes in the Results section of its test file, with fixes to the skills.
- A future model change needs a new eval run, because the skills are
  tuned for one model.
- `check_skill_style.py` failed on the 2 monkey skills before the fix,
  and on a scratch skill with a long description and 2 backslash paths.
