---
name: ml-critique-modeling
description: >-
  Modeling lens of ml-critique. Use to critique an ML modeling or solution
  report and its code: baseline, dataset and labels, split, leakage,
  features, model, loss, tuning, evaluation, serving, reproducibility.
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
   In a project folder, read `spec/`, `modeling/01`-`05`, and the PRD
   metrics. Use `01-data.json`'s `dataset` block for paths, label, and
   split.
2. Use the problem type's playbook in `../ml-playbooks.md`. Do its
   classic-mistakes check first. For complexity findings, use Principle 1
   in `../ml-design-principles.md` (the complexity gate, the cost table).
   For negatives, architecture, and training setup, the typical options
   and values are in `../ml-model-training.md`. For serving (mode, latency
   budget, capacity, cost): `../ml-serving.md`.
3. Do the checks in [references/catalog.md](references/catalog.md). The
   sections are in priority order: A to D (baseline, labels, split,
   leakage) hold most P1 findings. Inside a section, check the `[C]` items
   first (the most likely P1), then the others in ID order. Check all
   items.
4. Put each result in one part: done well, change or fix, missing, or
   question. Give each finding a priority with the remedy from the
   catalog. List a strength only if losing it would make the result
   worse, with what breaks if it is lost (the core's "Done well" rule).
   Do not list basic hygiene.
5. Add the playbook's questions that the report did not answer. Give each
   question the expected answer, why it matters, and what each likely
   answer changes (the core's part 4).
6. If a critique context is given, apply it. On a conflict with this lens,
   follow the context, and return the conflict: the rule, the context
   requirement, and what you did.

## Evidence

- With code or data: command output for each P1 and P2 finding. You can
  read any file (code, params, logs). Run no new training. Standard
  probes:
  - **Leakage:** train on the suspect feature only. A score near the full
    model shows a leak.
  - **Split:** count entities in both train and test. Compare date ranges.
  - **Baseline:** score the playbook baseline on the same test set.
  - **Noise:** bootstrap the metric, or run
    `python3 .agents/skills/personal/ml-modeling/scripts/hypothesis_tester.py`.
  - **Threshold:** compute precision and recall at the action capacity.
- Text-only write-up (no code or data, for example an interview report):
  evidence is a quote with `file:line` and arithmetic from the stated
  numbers. Show each calculation (for example the accuracy of a constant
  predictor at the sampled base rate). Reason: a probe needs data that
  does not exist, and a shown calculation lets the reader check it.

Run probes with `uv run`, and write them in the session scratchpad. Do not
change the project's code or data.

## Check

Before you return the critique, read it again against these questions. Fix each
"no", then check again (maximum 2 loops). Return the open items and each skill
issue (a gap or error in this lens or its catalog) with the critique. Return an
issue only if it made this critique worse: a missed, wrong, or late finding.
Reason: a gap that the playbook covered anyway adds noise to the log.
1. Does each check that you did have a result, or a one-line reason why
   it does not apply?
2. Does each P1 and P2 finding have the required evidence (probe output,
   or for a text-only write-up a quote and a shown calculation) and an
   alternative?
3. Did no probe change the project's code or data?
4. Are the findings sorted with the core's sort key (priority, then
   upstream in catalog section order, then effect, then confidence)? Does
   each question have an expected answer, why it matters, and what each
   answer changes?
5. Is each conflict with the critique context returned?

Done when the 5 answers are yes.
