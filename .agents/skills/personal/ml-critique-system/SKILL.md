---
name: ml-critique-system
description: >-
  System-design lens of ml-critique. Use to critique an ML system design
  write-up (PRD, design doc, RFC, or interview answer): goal, metrics,
  framing and labels, data, architecture, modeling plan, serving,
  delivery.
---

# ML Critique: System Lens

## Purpose

Find the decisions in a design write-up that are vague, wrong, or that can
give a large gain. `ml-critique` owns the procedure, the priority rule, and
the output. This lens owns what to look for. If `ml-critique` did not
dispatch you, run it first.

## Steps

1. Read `prd/`, `design/`, and `adr/` (or the given document) from start to
   end. An ADR that justifies a decision well is a strength, not a
   question.
2. Use the problem type's playbook in `../ml-playbooks.md`. Do its
   classic-mistakes check first. For complexity findings, use Principle 1
   in `../ml-design-principles.md` (the complexity gate, the cost table).
   For negatives, architecture, and training setup, the typical options
   and values are in `../ml-model-training.md`. For serving (mode, latency
   budget, capacity, cost): `../ml-serving.md`.
3. Do the checks in [references/catalog.md](references/catalog.md). The
   sections A (goal), B (metrics), and D (framing and labels) hold most P1
   findings. Do them first. Inside a section, check the `[C]` items first
   (classic mistakes: the most likely P1 or P2), then the others in ID
   order. Check all items.
4. Put each result in one part: done well, change or fix, missing, or
   question. Give each finding a priority with the remedy from the
   catalog. List a strength only if losing it would make the result
   worse, with what breaks if it is lost (the core's "Done well" rule).
   Do not list basic hygiene.
5. Add the playbook's questions that the write-up did not answer. Give each
   question the expected answer, why it matters, and what each likely
   answer changes (the core's part 4).
6. Do the cross-section checks (section K, the `[C]` items first).
   Errors across sections are often P1.
7. If a critique context is given, apply it. On a conflict with this lens,
   follow the context, and return the conflict: the rule, the context
   requirement, and what you did.

Evidence is a quote with `file:line`, or a section that is not there. You
can list source tables to confirm that they exist. Do not profile data.
For a number in the write-up, arithmetic from the stated numbers is
evidence (show the calculation).

## Check

Before you return the critique, read it again against these questions. Fix each
"no", then check again (maximum 2 loops). Return the open items and each skill
issue (a gap or error in this lens or its catalog) with the critique. Return an
issue only if it made this critique worse: a missed, wrong, or late finding.
Reason: a gap that the playbook covered anyway adds noise to the log.
1. Does each check that you did have a result, or a one-line reason why
   it does not apply?
2. Does each P1 and P2 finding have a quote with `file:line` (or a named
   missing section) and an alternative?
3. Are the findings sorted with the core's sort key (priority, then
   upstream in catalog section order, then effect, then confidence)?
4. Does each question have an expected answer, why it matters, and what
   each answer changes?
5. Is each conflict with the critique context returned?
6. Does each strength say what breaks if it is lost, with no basic hygiene
   and at most 5?

Done when the 6 answers are yes.
