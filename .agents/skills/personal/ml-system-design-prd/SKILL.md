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

This skill is the interview. It creates the project folder and writes
`prd/`. `ml-system-design-definition` owns the checklist. Use its
checklist, and keep no copy here.

Rules: `../ml-system-design/SKILL.md`, "Project folder", "Output docs",
"Check the output", "Skill improvement log".

## Steps

1. **Project folder.** Use the user's project name, or propose
   `ml-<topic-slug>`. The parent is `labs/` unless the user names another.
   If the folder exists, ask: continue it, or start a new attempt
   (`-<n>`)?
2. **Load.** Call the Skill tool 2 times: `ml-system-design-definition`
   (the checklist) and `grilling` (the interview mechanics).
3. **Seed the tree.** Each bullet of the `ml-system-design-definition`
   checklist is a branch, for the topic in `$ARGUMENTS`. Read the bullets
   from that skill each run. Reason: a copied list goes stale when the
   checklist changes. Include all branches, also when the topic seems
   obvious: the interview exists to stop silent assumptions.
4. **Grill** in rounds until the frontier is empty.
   - Regular: push for precise answers.
   - Quick POC: the same coverage, a faster pace. Make the one-pass POC draft of
     `ml-system-design-definition`. Show it as numbered questions, with the
     draft answer as the recommendation. Maximum 6 questions in each round (a
     bullet with sub-parts is one question). Accept the first reasonable answer.
   - End each round with: "Anything else to add or change before I move
     on?"
5. **Write** `<project-folder>/prd/<topic-slug>.md`: one heading for each
   checklist bullet, in the user's words and numbers, not draft
   assumptions: later steps treat the PRD as confirmed. Do not write
   `design/definition.md`. If the slug is ambiguous, confirm it.
6. **Check.**

## Answers in a notes file

The user can answer in a notes file (`@notes/<topic>.md`), and mix it
with chat answers. The file has the user's own section labels (for
example `#to-prd`).
1. Read the file. Match its content to the open questions by the labels.
2. Use only the content that was added since this session last read the
   file.
3. Say which questions the new content answered, and which are still
   open.

## Check

Do "Check the output" in `../ml-system-design/SKILL.md`. Intent questions:
1. Does each checklist bullet have a concrete answer that the user
   confirmed?
2. Does the problem name the decision that the model controls, and who
   acts on it?
3. Is there one primary offline metric, and does each metric have a
   threshold? Does the intended behavior name the ways to game the
   primary metric, each with a guardrail?
4. Is the out-of-scope list real and specific? Is the baseline named?

Done when the PRD file exists, the 4 answers are yes, and `check_doc.py`
prints `OK`.
