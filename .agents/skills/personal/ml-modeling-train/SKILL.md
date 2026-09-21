---
name: ml-modeling-train
description: >-
  Use to select and train one ML model candidate, sequentially — the
  algorithm-selection matrix, cross-validation, experiment logging. Step 3 of
  the ml-modeling-* chain (data → features → train → evaluate), the sequential
  alternative to ml-modeling-multiagent. Trigger on "train a model for this,"
  "pick an algorithm," or continuing modeling work in an existing
  ml-<topic>-<n>/ project.
---

# Train (sequential)

Reads `<project-folder>/design/high-level.md`'s Phasing (the model class per
phase: baseline, first real model, stretch), `modeling/01-data.md` (class
balance), and `modeling/02-features.md`. The candidate, loss, and class
weighting are this step's decisions, recorded in `03-train.md`. Writes
`<project-folder>/modeling/03-train.md`. Project folder and output format: see `../ml-modeling/SKILL.md`,
"Which project folder" and "Output docs". First, run the "Design docs
changed?" check from `../ml-modeling/SKILL.md`.

Train on `02-features.md`'s "Output table" if present, else `01-data.json`
-> `dataset.train`. Cross-validate inside that table only; `dataset.test` is
never read here - it belongs to `ml-modeling-evaluate`.

One candidate, chosen and trained in this single pass — see `ml-modeling` router
if you want `ml-modeling-multiagent` instead (multiple candidates, concurrent,
compared). Mode: Regular starts simple and upgrades only if the simple model
underperforms; Quick POC goes straight to the workhorse row below unless
high-level's Phasing says otherwise — see `ml-modeling` router for the keyword
rule. Class imbalance: decide the handling here (class weights first, resampling
only if weights underperform) from `01-data`'s class balance, and say why in
`03-train.md`.

## Algorithm selection

| Scenario | Start with | Upgrade to |
|---|---|---|
| Interpretability required | Logistic/Linear Regression | — (stay here for stakeholder-facing models) |
| Small data (<10K rows) | Random Forest | XGBoost if accuracy insufficient |
| Medium data, high accuracy needed | XGBoost/LightGBM | — (default workhorse for tabular data) |
| Large data, complex patterns | Neural network | Only once tree methods plateau |
| Unsupervised grouping | K-Means/DBSCAN | Validate `k` via silhouette score |

Use cross-validation, not a single train/test split, to pick between candidates.
Folds are drawn inside the train table, never across the `dataset` split.

Before trusting a CV ranking, check whether any feature in the table was
built from the target column without per-fold nesting (a leave-one-out or
target-encoded aggregate computed once, globally - see
`ml-modeling-features/SKILL.md`, "Aggregation features"). If so, either
recompute it per fold or treat the ranking as provisional pending the real
held-out evaluation in `ml-modeling-evaluate`, and say so explicitly in
`03-train.md` - don't pick a winner off unverified CV numbers. The
distortion this causes is not uniform across model classes: a
gradient-boosted/iterative model can exploit it far more than a bagged or
linear one, which is exactly the failure mode this check exists to catch.

## Quick POC time budget

Target roughly 3 minutes of wall-clock for the candidate, not left
unbounded. Neither the mode line above nor the algorithm-selection matrix
names a fold count or model size, so without an explicit default this
step silently reaches for Regular-mode-grade rigor (5-fold CV, 200
trees/iterations) even on a fast POC pass - real numbers from one project:
Random Forest (`n_estimators=200`, `max_depth=12`) took 237.6s for 5-fold
CV on a 480k-row table, HistGradientBoosting (`max_iter=200`) took 125.4s.
Default Quick POC to (1) 3-fold CV instead of 5-fold - cuts wall-clock by
~40% with only a small loss of estimate stability for a POC-grade
decision, and (2) roughly half the Regular-mode default trees/iterations
(e.g. `n_estimators=100` instead of 200 for Random Forest, `max_iter=100`
instead of 200 for HistGradientBoosting/LightGBM/XGBoost) unless the user
names a specific size. Applied to the numbers above, this would bring
Random Forest to roughly 70s and HistGradientBoosting to roughly 40s -
both comfortably under budget. Regular mode keeps the fuller defaults
(5-fold, 200 trees/iterations) since it isn't optimizing for speed. State
the reduced fold count and size explicitly in `03-train.md`'s params (not
silently) so a later Regular-mode re-run knows what was traded away.

## Log it

```
python3 ../ml-modeling/scripts/experiment_tracker.py \
  --log-file <project-folder>/modeling/experiments.json \
  log --name "<model>_v1" --params '{"lr":0.1,"depth":6}' \
  --metrics '{"f1":0.87}'
```

Every training run gets logged — this is what `ml-modeling-evaluate` and any
later run compare against. Always pass `--log-file` with the project's path, and
before the subcommand (`--log-file ... log ...`, not `log --log-file ...`, which
argparse rejects): the script's default is `experiments.json` relative to
whatever directory the agent happens to be in, which scatters logs across
projects.

Done when `03-train.md` names the chosen model, states why it beat the
alternatives in the matrix above (not just "it's the default"), includes the
training code actually run — not a template — and, if this step's choice of
model/loss/class-weighting resolves a placeholder or contradicts an
assumption in `spec/<topic>.md`, that spec line is updated to match (see
`../ml-modeling/SKILL.md`, "Spec self-staleness").

If this run turns up a bug or a better design in this skill, or you ask for a
change to how it works, log it — see `../ml-modeling/SKILL.md`'s Skill
improvement log.
