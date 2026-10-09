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
2. Use the problem type's playbook in
   `../ml-playbooks.md`. Do its classic-mistakes check
   first.
3. Do the checks in [references/catalog.md](references/catalog.md). The
   sections A (goal), B (metrics), and D (framing and labels) hold most P1
   findings. Do them first. Brief mode: `[C]` items, plus any P1 or P2
   found while reading.
4. Put each result in one part: done well, change or fix, missing, or
   question. Give each finding a priority with the remedy from the
   catalog.
5. Add the playbook's questions that the write-up did not answer, each with
   an expected answer.
6. Do the cross-section checks (section K). Errors across sections are
   often P1.

Evidence is a quote with `file:line`, or a section that is not there. You
can list source tables to confirm that they exist. Do not profile data.

Done when each check in the mode's scope has a result, or a one-line
reason why it does not apply.
