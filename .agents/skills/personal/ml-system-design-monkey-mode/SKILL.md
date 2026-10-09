---
name: ml-system-design-monkey-mode
description: >-
  One-shot, fully autonomous ML baseline builder - ask up to 3 quick questions,
  then build and evaluate a fast (5-10 min) baseline in the background while
  the user keeps working. Always asks the user which data to use and waits
  for that answer; the other questions never block. A third, independent
  track alongside the whole-design path and the ml-modeling-* path. Run by hand only, e.g. /ml-system-design-monkey-mode
  churn prediction for a subscription app.
disable-model-invocation: true
---

# Monkey Mode

Contents: Steps | The 3 questions (only the data choice blocks) | Fast
defaults (build with these; do not ask) | Saved outputs: eval runs again
without modeling | Deliverable | Check

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
[ ] 2 Ask the 3 questions (wait only for the data choice)
[ ] 3 Dispatch the background agent
[ ] 4 Report the results, the Check result, and the skill issues
```

1. **Project folder.** Resolve it with `../ml-system-design/SKILL.md`,
   "Project folder" (name, parent, new attempt).
2. **Ask the 3 questions** (below) with AskUserQuestion, each with a
   recommended default.
   - **The data choice blocks.** Wait for the user's answer to "which
     data?". Never pick the data yourself, not even a synthetic set
     (user decision, 2026-10-09).
   - The metric and the success bar never block: for each one without an
     answer, use the self-inferred default. Do not ask again.
3. **Dispatch** a background `general-purpose` agent. No worktree is
   necessary: it is one script. Give it:
   - the task, data, metric, and success bar, each marked
     "answered by user" or "self-inferred";
   - the fast defaults, the saved-output rules, the deliverable, the
     Check, and the output path;
   - this rule: **the agent does not write `report.md`.** It writes the
     code, the logs and the metrics files, and returns the full
     `report.md` text in its final message. Claude Code blocks subagents
     from writing report files.

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
4. **Save and report.** When the agent finishes, save its returned text
   verbatim to `<project-folder>/monkey-mode/report.md`, run
   `check_doc.py` on it (see "Check"), then report the results. Add each
   skill issue that the agent reports to the skill improvement log.

## The 3 questions (only the data choice blocks)

1. **Task and data:** what is predicted, and which data is used?
   - Task: take the task type (classification, regression, ranking) from
     the request.
   - Data: always ask, and wait for the answer. Offer concrete options:
     - the user's own path, if the request or the project names one;
     - 1-2 public proxy datasets with real labels of the same shape, each
       named, cited, and sized (for example Wikipedia Clickstream for
       next-page recommendation, about 0.5 GB a month);
     - a small synthetic dataset, with its limit stated: synthetic labels
       only replay what the generator encoded, so the baseline number
       says little for recommender and text tasks.
   - Put the recommended option first, with the reason.
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
- **Ranking scored with graded nDCG:** train on the graded target
  (regression on `log1p` of the relevance, or LambdaMART), not a binary
  "clicked or not" label. A binary label can't order candidates by
  volume (measured: -5.8% to -8% nDCG in the Riot wiki project).
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

`<project-folder>/monkey-mode/report.md`, saved by the main session from
the agent's returned text, with these 7 sections:

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

Done when the 4 answers are yes, the main session has saved `report.md`,
and `check_doc.py` prints `OK` for it with:

```
--sections "Requirements,Input,Design,Implementation,Results,Learnings,Suggested Next Steps"
```
