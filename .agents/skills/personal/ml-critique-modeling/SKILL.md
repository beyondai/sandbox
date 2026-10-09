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
2. Use the problem type's playbook in
   `../ml-playbooks.md`. Do its classic-mistakes check
   first.
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

- Brief mode: `file:line` or a number from existing output. Run no new
  commands.
- Normal mode: command output for each P1 and P2 finding. Standard probes:
  - **Leakage:** train on the suspect feature only. A score near the full
    model shows a leak.
  - **Split:** count entities in both train and test. Compare date ranges.
  - **Baseline:** score the playbook baseline on the same test set.
  - **Noise:** bootstrap the metric, or use
    `../ml-modeling/scripts/hypothesis_tester.py`.
  - **Threshold:** compute precision and recall at the action capacity.

Run probes with `uv run`, and write them in the session scratchpad. Do not
change the project's code or data.

Done when each check in the mode's scope has a result, or a one-line reason
why it does not apply, and each P1 and P2 finding has the evidence that the
mode requires.
