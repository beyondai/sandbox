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

- **Reads:** the Phasing in `<project-folder>/design/high-level.md`,
  `modeling/01-data.md` (class balance), and `modeling/02-features.md`.
- **Input table:** the "Output table" in `02-features.md`, or else
  `01-data.json` -> `dataset.train`. Give this path to each candidate.
  Never read `dataset.test`.
- **Writes:** `modeling/03-train.md` (the same file as `ml-modeling-train`)
  and `modeling/train-candidates/<model-type>/`.
- **Rules:** `../ml-system-design/SKILL.md`, "Project folder", "Output
  docs", "Check the output", "Skill improvement log".

Use this skill when several candidates are reasonable, or when speed
matters (Quick POC). Each candidate writes only to its own folder, so no
git worktree is necessary.

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
   - trains its candidate with CV inside the input table;
   - computes the metrics that `ml-modeling-evaluate` uses;
   - writes code and `metrics.json` to `train-candidates/<model-type>/`;
   - reports its metrics.

   Quick POC: tell each candidate to target about 3 minutes. Use 3-fold CV
   and about half the trees or iterations (for example `n_estimators=100`,
   not 200), unless the user names a size. Write the folds and the size in
   `metrics.json` and in the candidate's entry in `03-train.md`. Regular
   uses 5-fold and 200.
5. **Compare.** Make a table: model type, primary metric with its noise,
   training time, inference cost, explainability. Rank by the primary
   offline metric in `prd/<topic>.md`.
   - Select the simplest candidate inside the noise of the best, unless a
     more complex one passes the complexity gate
     (`../ml-design-principles.md`, Principle 1).
   - If the result is close, show the table and let the user select.
   - **CV leak check.** Is a feature built from the target once for
     the whole table (leave-one-out or target encoding)? A boosted
     candidate uses this leak more than a linear or bagged one, so the
     winner can be wrong. Compute the feature again in each fold, or mark
     the ranking as provisional in `03-train.md`.
6. **Write `03-train.md`:** the table, the winner, why it won, and the
   winner's training code. Other candidates' code stays in
   `train-candidates/`.
7. **Log** each candidate. Put `--log-file` before the subcommand.
   `compare --ids` queries them later.

   ```
   python3 .agents/skills/personal/ml-modeling/scripts/experiment_tracker.py \
     --log-file <project-folder>/modeling/experiments.json log ...
   ```

8. **Check.**

## Check

Do "Check the output" in `../ml-system-design/SKILL.md`. Intent questions:
1. Did each candidate train, with real metrics in the table (no
   placeholders)?
2. Is a simple candidate in the table?
3. Does `03-train.md` say why the winner won? Does a complex winner pass
   the complexity gate?
4. Is the CV free of the target leak, or is the ranking marked
   provisional?

Done when the 4 answers are yes, `check_doc.py` prints `OK`, and a spec
line that the winner resolves or contradicts is updated (see "Closing the
loop" in `../ml-modeling/SKILL.md`).
