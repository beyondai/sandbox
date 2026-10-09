---
name: ml-critique-system
description: >-
  System-design lens of ml-critique. Use to critique an ML system design
  write-up (PRD, design doc, RFC, or interview answer): goal, metrics,
  framing and labels, data, architecture, modeling plan, delivery.
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
   and values are in `../ml-model-training.md`.
3. Do the checks in [references/catalog.md](references/catalog.md). The
   sections A (goal), B (metrics), and D (framing and labels) hold most P1
   findings. Do them first. Brief mode: `[C]` items, plus any P1 or P2
   found while reading.
4. Put each result in one part: done well, change or fix, missing, or
   question. Give each finding a priority with the remedy from the
   catalog.
5. Add the playbook's questions that the write-up did not answer, each with
   an expected answer.
6. Do the cross-section checks (section K; Brief: the `[C]` items). Errors
   across sections are often P1.

Evidence is a quote with `file:line`, or a section that is not there. You
can list source tables to confirm that they exist. Do not profile data.

## Check

Before you return the critique, read it again against these questions. Fix each
"no", then check again (maximum 2 loops). Return the open items and each skill
issue (a gap or error in this lens or its catalog) with the critique. The core
logs them.
1. Does each check in the mode's scope have a result, or a one-line
   reason why it does not apply?
2. Does each P1 and P2 finding have a quote with `file:line` (or a named
   missing section) and an alternative?
3. Are the findings in priority order, upstream (catalog section order)
   first?
4. Does each question have an expected answer?

Done when the 4 answers are yes.
