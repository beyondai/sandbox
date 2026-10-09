---
name: ml-system-design-monkey-mode
description: >-
  One-shot, fully autonomous ML baseline builder - ask up to 3 quick questions,
  then build and evaluate a fast (5-10 min) baseline in the background while you
  keep working. Never blocks - proceeds with self-inferred assumptions if you
  don't answer. A third, independent track alongside the whole-design path and
  the ml-modeling-* path. Run by hand only, e.g. /ml-system-design-monkey-mode
  churn prediction for a subscription app.
disable-model-invocation: true
---

# Monkey Mode

Contents: Steps | The 3 questions (never blocking) | Fast defaults (build with
these; do not ask) | Saved outputs: eval runs again without modeling |
Deliverable | Check

One line in, a runnable baseline out, in the background, while the user
works on the real design.

- An independent track. It shares only the project folder with
  `ml-system-design-*` and `ml-modeling-*`. It does not read `design/` or
  `prd/`, and it writes only `monkey-mode/`. Nothing must run first.
- For high-cardinality id columns (user or item ids, recommendation
  problems), use `ml-system-design-monkey-mlp`. It has the same contract
  and writes `monkey-mlp/`, so both can run on one project.
- Rules: `../ml-system-design/SKILL.md`, "Project folder", "Output docs",
  "Check the output", "Skill improvement log".

## Steps

Progress (copy into your reply, tick each line):

```
[ ] 1 Resolve the project folder
[ ] 2 Ask the 3 questions (never block)
[ ] 3 Dispatch the background agent
[ ] 4 Report the results, the Check result, and the skill issues
```

1. **Project folder.** Resolve it with `../ml-system-design/SKILL.md`,
   "Project folder" (name, parent, new attempt).
2. **Ask the 3 questions** (below) with AskUserQuestion, each with a
   recommended default. Never block: the baseline runs while the user
   works on other things. For each item without an answer, use the
   self-inferred default. Do not ask again.
3. **Dispatch** a background `general-purpose` agent. No worktree is
   necessary: it is one script. Give it:
   - the task, data, metric, and success bar, each marked
     "answered by user" or "self-inferred";
   - the fast defaults, the saved-output rules, the deliverable, the
     Check, and the output path.

   Tell the agent that the project folder is shared and in progress.
   Other work (the PRD, the design) can write there at the same time:
   - Never delete or reset the project folder or a sibling folder
     (`prd/`, `design/`, `adr/`, `spec/`, `modeling/`).
   - Create only `monkey-mode/` with `mkdir -p`, and write only there.
   - "The folder does not exist yet" describes the state before the run.
     It does not permit a reset.

   Tell the agent to run `uv run python3 -c "import pandas, numpy, sklearn"`
   from the project folder (the shared sandbox venv). Only if this fails,
   run `uv add <pkg>` at the sandbox root, and record it in Learnings. Do
   not make a project venv: it duplicates work and drifts from the shared
   environment.

   Tell the user that it runs in the background.
4. **Report** the results when the agent finishes. Add each skill issue
   that the agent reports to the skill improvement log.

## The 3 questions (never blocking)

1. **Task and data:** what is predicted, and where is the data?
   - Default: take the task type (classification, regression, ranking)
     from the request. With no data, generate a small synthetic dataset
     shaped like the problem.
2. **Primary metric:** what is the baseline scored on?
   - Default: F1 for imbalanced binary classification, RMSE for
     regression, nDCG for ranking.
3. **Success bar:** what is "good enough" for a first baseline? 3 ways to
   answer:
   - a number that the user has;
   - "look one up": a web search for a domain benchmark, at most 2
     minutes. Take the best citation in that time. Convert it to the
     metric, as a soft target. If the benchmark measures a different
     population (for example new-install churn against retained-player
     lapse), say so, and do not adopt the number;
   - the default: an assumed number for this problem and data (for
     example "F1 ~0.65-0.75 for a roughly balanced synthetic binary
     classification"), not only "beat random".

A runnable result with a real number is more important than a good
number. Each other choice (cleaning, transforms, model, split, sample) is
a stated assumption, never a 4th question.

## Fast defaults (build with these; do not ask)

- **Cleaning:** drop the nulls, or impute the median.
- **Features:** standard-scale numerics. One-hot low-cardinality
  categoricals. No embeddings.
- **Model:** one fast model, trained once: the "start simple" row in
  the matrix of `../ml-modeling-train/SKILL.md` (logistic or linear
  regression, or one small tree ensemble). No comparison.
- **Eval:** a held-out split, or a sample for a large dataset, scored on
  the primary metric. For a sample, state its size in the Requirements
  and Input sections as a bold percentage of the full source. Example:
  "**a 600,000-row sample, ~8.1% of the full 7,377,419-row
  `train.csv`**". Not only a raw row count in Next Steps: readers compare
  the result with benchmarks on the full data.

## Saved outputs: eval runs again without modeling

A change of metric or cutoff (for example @10 to @5) runs the eval
again, never data prep or training. The code has 2 entry points:

```
train:  prepare data -> split -> fit -> score -> save   (slow, run once)
eval:   read saved outputs -> metrics at any K -> metrics file   (fast)
```

- Save as parquet:
  - the prepared and split data (with the split column);
  - the ground truth for the eval rows or queries;
  - the candidate sets, for ranking;
  - each model's scores: the top 50 items for each query (ranking), or
    each eval row (classification, regression).
- Save them in the sandbox-root `data/<dataset>/monkey-mode/`, never in
  the project folder.
- Before the run ends, run `git check-ignore -v <path>` for each saved
  path. If a path is not
  ignored, move it under `data/`. Do not edit `.gitignore` without the
  user's approval.
- The project folder keeps only small files: code, the metrics file, the
  run log, `report.md`.
- Name the saved paths and the `eval` command in Implementation.

## Deliverable

`<project-folder>/monkey-mode/report.md`, with these 7 sections:

- **Requirements:** from the 3 answers or their defaults. Mark each item
  "answered by user" or "self-inferred".
- **Input:** the data path, or the synthetic generator and its seed.
- **Design:** the approach and why (the fast defaults for this problem).
- **Implementation:** the code that ran, not a template.
- **Results:** real metrics against the success bar.
- **Learnings:** what the baseline shows (is the target learnable, data
  issues, surprises).
- **Suggested Next Steps:** what this means for the regular flow (for
  example "the V1 model class in the Phasing of `design/high-level.md` is
  a reasonable bet"). Monkey-mode never reads or writes `design/`,
  `modeling/`, `prd/`, `adr/`, or `spec/`.

## Check

The background agent does "Check the output" in
`../ml-system-design/SKILL.md`. It does not ask the user, and it reports
each skill issue in its final message (not in a file). Intent questions:
1. Do all 7 sections hold results of a real run (real code, real
   numbers)?
2. Is each Requirements item marked "answered by user" or
   "self-inferred"?
3. Is the result compared with the success bar, and is a sample stated as
   a percentage?
4. Do the saved outputs exist and are they git-ignored? Does the `eval`
   entry point make the same metrics file again?

Done when the 4 answers are yes and `check_doc.py` prints `OK` for
`report.md` with:

```
--sections "Requirements,Input,Design,Implementation,Results,Learnings,Suggested Next Steps"
```
