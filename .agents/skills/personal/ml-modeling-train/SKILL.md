---
name: ml-modeling-train
description: >-
  Use to select and train one ML model candidate, sequentially - the
  algorithm-selection matrix, cross-validation, experiment logging. Step 3 of
  the ml-modeling-* chain (data → features → train → evaluate → serve), the
  sequential
  alternative to ml-modeling-multiagent. Trigger on "train a model for this,"
  "pick an algorithm," or continuing modeling work in an existing
  ML project folder.
---

# Train (sequential)

Contents: Algorithm selection | Ranking tasks | Record the training setup |
Quick POC time budget | Log each run | Check

- **Reads:** the Phasing in `<project-folder>/design/high-level.md` (the
  model class for each phase), `modeling/01-data.md` (class balance), and
  `modeling/02-features.md`.
- **Input table:** the "Output table" in `02-features.md`, or else
  `01-data.json` -> `dataset.train`. Cross-validate inside this table.
  Never read `dataset.test`: it belongs to `ml-modeling-evaluate`.
- **Writes:** `modeling/03-train.md` and `modeling/model.joblib` (the
  fitted model and its decision threshold; see "Handoff" in
  `../ml-modeling/SKILL.md`).
- **Rules:** `../ml-system-design/SKILL.md`, "Project folder", "Output
  docs", "Check the output", "Skill improvement log".
- **Mode:** Regular starts simple. It selects a more complex model only if
  it passes the complexity gate (`../ml-design-principles.md`, Principle 1:
  the gain is larger than the noise, and the value of the gain is larger
  than the added running, maintenance, explainability, and risk cost).
  Quick POC goes to the workhorse row (below), unless the Phasing says
  otherwise.

This skill selects one model. It also trains the simplest option (a
linear model or the playbook baseline) as the comparison, so the choice
has evidence. For several candidates in parallel, use
`ml-modeling-multiagent` ("When to use" there). If the Phasing names 2 or
more model classes and the user did not choose, suggest it in one line.

**Threshold.** For a metric at a threshold (F1, precision@k), choose the
threshold on out-of-fold train predictions, never on test. Save it in
`model.joblib`.

Steps:
1. Run "Design docs changed?" in `../ml-modeling/SKILL.md`.
2. Select the candidate (matrix below). Decide the loss and the class
   imbalance handling: class weights first; resampling only if weights do
   worse. Start from the hyperparameters, architecture, and training
   setup in `../ml-model-training.md`. Say why in `03-train.md`.
3. Check the CV for leaks (below).
4. Train with CV. Log each run.
5. Write `03-train.md`, with the cost table if the selected model is not
   the simplest one tried.
6. Check.

## Algorithm selection

| Scenario | Start with | Upgrade to |
|---|---|---|
| Interpretability required | Logistic/Linear Regression | none (stay for stakeholder-facing models) |
| Small data (<10K rows) | Random Forest | XGBoost if accuracy is not sufficient |
| Medium data, high accuracy needed | XGBoost/LightGBM | none (default workhorse for tabular data) |
| Large data, complex patterns | Neural network | only after tree methods plateau |
| Unsupervised grouping | K-Means/DBSCAN | validate `k` with the silhouette score |
| Ranking: (query, candidate) rows | GBDT regression on the graded label | LambdaMART (listwise loss) |

Use cross-validation, not one train/test split, to compare candidates.
Make the folds inside the train table, never across the `dataset` split.

**LightGBM or XGBoost: check that it loads.** Run
`uv run python3 -c "import lightgbm"` (or `xgboost`) before you pick it.
On macOS the wheel needs the system library `libomp`; without it, the
import fails after a clean install. A system library is the user's
decision (this user: `homebrew.brews` in the nix-darwin config). Ask; do
not install it. If it can't load, remove the package again
(`uv remove`) and use scikit-learn's `HistGradientBoosting`.

**CV leak check.** Is a feature built from the target once for the
whole table, without per-fold computation (a leave-one-out or target
encoding; see `../ml-modeling-features/SKILL.md`, "Aggregation features")?
If yes, compute it again in each fold, or mark the CV ranking as
provisional in `03-train.md` until `ml-modeling-evaluate`. A boosted model
uses this leak more than a linear or bagged model, so the ranking can be
wrong.

## Ranking tasks

One row is a (query, candidate) pair, and `dataset.group` names the query
column (`../ml-modeling-data/SKILL.md`).

- **Folds:** `GroupKFold` by `dataset.group`, so no query is in both the
  fit part and the scored part.
- **Metric:** per query (nDCG@K at the panel or page size), then the mean.
  Weight by segment when the PRD defines segments.
- **Target:** the graded label (for example `log1p` of a count), not a
  binary "clicked" label. A binary label can't order candidates by volume
  (measured: -5.8% to -8% nDCG in one project).
- **Simplest option:** the PRD baseline rule, scored on the same folds.
- **Threshold:** none. Save `threshold: None` in `model.joblib`.
- The nDCG over the candidates alone hides the candidate misses. Say so in
  `03-train.md`; `ml-modeling-evaluate` scores against the full truth.

## Record the training setup

In `03-train.md`, write (the "What to record" list in
`../ml-model-training.md`):
- the architecture and why;
- the key hyperparameters (trees: trees, depth, leaves, min leaf, learning
  rate and rounds; linear: regularization `C`; neural network: framework,
  optimizer, learning rate and schedule, batch size, epochs and early
  stopping, dropout, weight decay);
- the hardware (CPU, GPU, MPS), the wall-clock training time, and the
  tuning budget (trials, search method);
- the inference time: 1-row predictions on about 200 input rows after a
  short warm-up (p50 and p99 in ms), the model size, and a comparison
  with the PRD p99. A model over the target needs the user's acceptance:
  step 5 (`ml-modeling-serve`) measures the full path and would fail it.

## Quick POC time budget

Target about 3 minutes of wall-clock time for the candidate.

| Setting | Quick POC | Regular |
|---|---|---|
| CV folds | 3 | 5 |
| Trees or iterations | 100 (`n_estimators`, `max_iter`) | 200 |

The user can name another size. Write the folds and the size in the
params of `03-train.md`, so a Regular run knows what was reduced.
(Measured on 480k rows, 5-fold, 200 trees: Random Forest 237.6s,
HistGradientBoosting 125.4s. The POC settings bring them to about 70s and
40s.)

## Log each run

```
python3 .agents/skills/personal/ml-modeling/scripts/experiment_tracker.py \
  --log-file <project-folder>/modeling/experiments.json \
  log --name "<model>_v1" --params '{"lr":0.1,"depth":6}' \
  --metrics '{"f1":0.87}'
```

- Always give `--log-file` with the project path. The default path is
  relative to the current folder.
- Put `--log-file` before the subcommand. `log --log-file ...` fails.

## Check

Do "Check the output" in `../ml-system-design/SKILL.md`. Intent questions:
1. Does `03-train.md` name the selected model and compare it with the
   simplest option on the same CV (not "it is the default")?
2. If the model is not the simplest one tried, does the cost table show
   that it passes the complexity gate?
3. Does `03-train.md` hold the training code that ran, not a template?
   Does it record the hyperparameters or training setup, the hardware,
   the training time, and the inference time against the PRD p99?
4. Did no step read `dataset.test`? Is the threshold from out-of-fold
   predictions, and is `model.joblib` saved? Is the CV free of the leak
   above, or marked provisional?

Done when the 4 answers are yes, `check_doc.py` prints `OK`, and a spec
line that the model, loss, or class weights resolve or contradict is
updated (see "Closing the loop" in `../ml-modeling/SKILL.md`).
