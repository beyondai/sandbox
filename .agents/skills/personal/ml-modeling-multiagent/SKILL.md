---
name: ml-modeling-multiagent
description: >-
  Use to train and compare multiple ML model candidates concurrently instead of
  one at a time - dispatches one subagent per candidate, then merges results.
  Parallel alternative to ml-modeling-train for step 3 of the ml-modeling-*
  chain. Trigger on "try a few models in parallel," "compare multiple algorithms
  at once," or "multiagent"/"concurrent" training in an existing ML project
  folder.
---

# Train (parallel, multiple candidates)

Contents: When to use | Steps | Check

- **Reads:** the Phasing in `<project-folder>/design/high-level.md`,
  `modeling/01-data.md` (class balance), and `modeling/02-features.md`.
- **Input table:** the "Output table" in `02-features.md`, or else
  `01-data.json` -> `dataset.train`. Give this path to each candidate.
  Never read `dataset.test`.
- **Writes:** `modeling/03-train.md` and `modeling/model.joblib` (the
  same files as `ml-modeling-train`; see "Handoff" in
  `../ml-modeling/SKILL.md`), and `modeling/train-candidates/<model-type>/`.
  Evaluate and serve load `model.joblib`, so this route must save it.
- **Rules:** `../ml-system-design/SKILL.md`, "Project folder", "Output
  docs", "Check the output", "Skill improvement log".

Each candidate writes only to its own folder, so no git worktree is
necessary.

## When to use

Use this skill when:
- several candidates are reasonable: the Phasing names more than one
  model class, or the data does not show if a linear model or GBDT wins;
- speed matters (Quick POC): the candidates run at the same time, so the
  total time is close to that of one candidate;
- the choice needs evidence: the table compares metric with noise,
  training time, inference time, and explainability.

Use `ml-modeling-train` instead when:
- one candidate is the clear choice (the playbook and the Phasing agree);
- the session cannot give subagents write access (see step 3);
- token cost matters: each subagent reads the features and trains on its
  own, so the cost grows with the number of candidates.

If the user did not choose and the Phasing names 2 or more model classes,
suggest this skill in one line, then follow the user's answer.

## Steps

1. **Design docs changed?** Run the check in `../ml-modeling/SKILL.md`.
2. **List the candidates.** Each model class in the Phasing. If the
   Phasing names only one, add the short list from the matrix in
   `../ml-modeling-train/SKILL.md`. Always include one simple candidate (a
   linear model or a default GBDT): `../ml-design-principles.md`,
   Principle 1.
3. **Confirm that the session can execute.** Subagents get the
   permission state of this session. In plan mode or another restricted
   mode, they write a plan and stop, and report a normal completion. If
   the session is not in auto mode, tell the user and wait. Also make one
   small write first (for example, create `train-candidates/`). If it
   fails, tell the user and wait. A stuck subagent cannot fix this: an
   approval that another agent relays is not the permission system.
4. **Dispatch.** One subagent for each candidate, all in the same turn
   (parallel tool calls). Each subagent:
   - reads `modeling/02-features.md`;
   - trains its candidate with CV inside the input table, starting from
     `../ml-model-training.md` and the same tuning budget as the others
     (ranking tasks: folds by query, per `../ml-modeling-train/SKILL.md`,
     "Ranking tasks"; LightGBM or XGBoost: the import check there);
   - computes the metrics that `ml-modeling-evaluate` uses;
   - times its inference: 1-row predictions on about 200 input rows after
     a short warm-up (p50 and p99 in ms), and the model size;
   - writes code and `metrics.json` (with its hyperparameters, hardware,
     training time, and inference time) to
     `train-candidates/<model-type>/`;
   - reports its metrics.

   Quick POC: tell each candidate to target about 3 minutes. Use 3-fold CV
   and about half the trees or iterations (for example `n_estimators=100`,
   not 200), unless the user names a size. Write the folds and the size in
   `metrics.json` and in the candidate's entry in `03-train.md`. Regular
   uses 5-fold and 200.
5. **Compare.** Make a table: model type, primary metric with its noise,
   training time, inference time (1-row p99) and model size,
   explainability. Rank by the primary offline metric in
   `prd/<topic>.md`.
   - A candidate whose 1-row p99 is over the PRD p99 (or the ranking stage
     budget in `../ml-serving.md`) does not win unless the user accepts
     it. Reason: step 5 (`ml-modeling-serve`) would then fail the target.
     Step 5 measures the full path; this is an early, rough filter.
   - Select the simplest candidate inside the noise of the best, unless a
     more complex one passes the complexity gate
     (`../ml-design-principles.md`, Principle 1).
   - If the result is close, show the table and let the user select.
   - **CV leak check.** Is a feature built from the target once for
     the whole table (leave-one-out or target encoding)? A boosted
     candidate uses this leak more than a linear or bagged one, so the
     winner can be wrong. Compute the feature again in each fold, or mark
     the ranking as provisional in `03-train.md`.
6. **Save the winner.** Refit it on the whole input table. Choose its
   threshold on out-of-fold predictions, never on test (as in
   `../ml-modeling-train/SKILL.md`, "Threshold"). Save the model and the
   threshold in `modeling/model.joblib`.
7. **Write `03-train.md`:** the table, the winner, why it won, and the
   winner's training code. Other candidates' code stays in
   `train-candidates/`.
8. **Log** each candidate. Put `--log-file` before the subcommand.
   `compare --ids` queries them later.

   ```
   python3 .agents/skills/personal/ml-modeling/scripts/experiment_tracker.py \
     --log-file <project-folder>/modeling/experiments.json log ...
   ```

9. **Check.**

## Check

Do "Check the output" in `../ml-system-design/SKILL.md`. Intent questions:
1. Did each candidate train, with real metrics in the table (no
   placeholders)?
2. Is a simple candidate in the table?
3. Does `03-train.md` say why the winner won? Does a complex winner pass
   the complexity gate?
4. Is the CV free of the target leak, or is the ranking marked
   provisional?
5. Is `model.joblib` saved with the winner and its out-of-fold threshold?
   Does the table give each candidate's inference time, and is a
   candidate over the latency target kept out of the win (or accepted by
   the user)?

Done when the 5 answers are yes, `check_doc.py` prints `OK`, and a spec
line that the winner resolves or contradicts is updated (see "Closing the
loop" in `../ml-modeling/SKILL.md`).
