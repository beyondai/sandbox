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
`<project-folder>/modeling/03-train.md`.
First, run the "Design docs changed?" check from `../ml-modeling/SKILL.md`.

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
alternatives in the matrix above (not just "it's the default"), and includes the
training code actually run — not a template.

If this run turns up a bug or a better design in this skill, or you ask for a
change to how it works, log it — see `../ml-modeling/SKILL.md`'s Skill
improvement log.
