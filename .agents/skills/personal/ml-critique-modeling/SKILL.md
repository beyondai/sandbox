---
name: ml-critique-modeling
description: >-
  Modeling lens of ml-critique. Use to critique an ML modeling or solution
  report and its code: baseline, dataset and labels, split, leakage,
  features, model, loss, tuning, evaluation, reproducibility.
---

# ML Critique: Modeling Lens

## Purpose

Find the modeling decisions that are vague, wrong, or that can give a large
gain, and prove each important finding with the code and the data.
`ml-critique` owns the procedure, the priority rule, and the output. This
lens owns what to look for and how to prove it. If `ml-critique` did not
dispatch you, run it first.

## Steps

1. Read the report from start to end, then the code that made each number.
   In a project folder, read `spec/`, `modeling/01`-`04`, and the PRD
   metrics. Use `01-data.json`'s `dataset` block for paths, label, and
   split.
2. Use the problem type's playbook in `../ml-playbooks.md`. Do its
   classic-mistakes check first. For complexity findings, use Principle 1
   in `../ml-design-principles.md` (the complexity gate, the cost table).
   For negatives, architecture, and training setup, the typical options
   and values are in `../ml-model-training.md`.
3. Do the checks in [references/catalog.md](references/catalog.md). The
   sections are in priority order: A to D (baseline, labels, split,
   leakage) hold most P1 findings. Brief mode: `[C]` items, plus any P1
   or P2 found while reading.
4. Put each result in one part: done well, change or fix, missing, or
   question. Give each finding a priority with the remedy from the
   catalog.
5. Add the playbook's questions that the report did not answer, each with
   an expected answer.

## Evidence

- Brief mode: `file:line` or a number from existing output. You can read
  any file (code, params, logs). Run no probes or new training.
- Normal mode: command output for each P1 and P2 finding. Standard probes:
  - **Leakage:** train on the suspect feature only. A score near the full
    model shows a leak.
  - **Split:** count entities in both train and test. Compare date ranges.
  - **Baseline:** score the playbook baseline on the same test set.
  - **Noise:** bootstrap the metric, or run
    `python3 .agents/skills/personal/ml-modeling/scripts/hypothesis_tester.py`.
  - **Threshold:** compute precision and recall at the action capacity.

Run probes with `uv run`, and write them in the session scratchpad. Do not
change the project's code or data.

## Check

Before you return the critique, read it again against these questions. Fix each
"no", then check again (maximum 2 loops). Return the open items and each skill
issue (a gap or error in this lens or its catalog) with the critique. The core
logs them.
1. Does each check in the mode's scope have a result, or a one-line
   reason why it does not apply?
2. Does each P1 and P2 finding have the evidence that the mode requires
   (Brief: `file:line` or existing output; Normal: probe output) and an
   alternative?
3. Did no probe change the project's code or data?
4. Are the findings in priority order, upstream (catalog section order)
   first? Does each question have an expected answer?

Done when the 4 answers are yes.
