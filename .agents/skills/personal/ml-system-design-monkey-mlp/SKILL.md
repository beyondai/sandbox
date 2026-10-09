---
name: ml-system-design-monkey-mlp
description: >-
  One-shot, fully autonomous embedding-MLP baseline builder - ask up to 3
  quick questions, then build and evaluate a fast (10-15 min) PyTorch
  embedding-MLP baseline in the background while you keep working. Never
  blocks - proceeds with self-inferred assumptions if you don't answer. A
  sibling to ml-system-design-monkey-mode: same fast/autonomous contract, but
  learned categorical embeddings instead of one-hot + a tree/linear model -
  reach for it when the task has high-cardinality identity columns (user/item
  ids, recommendation-shaped problems). Run by hand only, e.g.
  /ml-system-design-monkey-mlp song repeat-listen prediction.
disable-model-invocation: true
---

# Monkey MLP

Contents: When to use it | Steps | Fast defaults (build with these; do not ask)
| Eval rules (mandatory) | Deliverable | Check

The same contract as `ml-system-design-monkey-mode` (independent,
background, never blocks), with a small PyTorch embedding-MLP as the
model. Each categorical column gets a learned embedding, concatenated with
standardized numerics, through a small MLP head.

- Writes only `monkey-mlp/`. Reads nothing in `design/`, `prd/`, or
  `modeling/`. It can run alone or next to monkey-mode on the same project
  (different folders), for a tree-vs-embedding comparison.
- Rules: `../ml-system-design/SKILL.md`, "Project folder", "Output docs",
  "Check the output", "Skill improvement log".

## When to use it

Use monkey-mode's tree or linear default in most cases: no early
stopping, no architecture choice, one `.fit()`. Use monkey-MLP when the
task has **high-cardinality identity columns** (user ids, item or song
ids, thousands of unique values or more): recommendation, repeat purchase
or repeat listen, problems shaped like collaborative filtering.

Expect "close to a tuned model with no feature work", not "better". On
KKBOX repeat-listen (480K train, 120K test rows), it got AUC 0.7271
against 0.7361 for a feature-engineered Random Forest. The embeddings
learned what the hand-built `msno_repeat_rate` and `song_repeat_rate`
columns gave.

## Steps

Progress (copy into your reply, tick each line):

```
[ ] 1 Resolve the project folder
[ ] 2 Ask the 3 questions (never block)
[ ] 3 Dispatch the background agent
[ ] 4 Report the results, the Check result, and the skill issues
```

1. **Project folder:** as in monkey-mode.
2. **The 3 questions:** use "The 3 questions" in
   `../ml-system-design-monkey-mode/SKILL.md` (task and data, primary
   metric, success bar), with AskUserQuestion. Never block.
3. **Dispatch** a background `general-purpose` agent. Give it the
   resolved answers (each marked "answered by user" or "self-inferred"),
   the fast defaults, the eval rules, the deliverable, the Check, and the
   output path.
   - The project folder is shared and in progress. Never delete or reset
     the folder or a sibling (`prd/`, `design/`, `adr/`, `spec/`,
     `modeling/`, `monkey-mode/`). Create only `monkey-mlp/` with
     `mkdir -p`, and write only there.
   - Run `uv run python3 -c "import pandas, numpy, sklearn, torch"` from
     the project folder (the shared sandbox venv has `torch==2.2.2`, with
     MPS). Only if it fails, run `uv add torch` at the sandbox root. Do
     not make a project venv.
   - Device: `"mps"` if `torch.backends.mps.is_available()`, else
     `"cuda"` if `torch.cuda.is_available()`, else `"cpu"`.
4. **Report** the results. Add each skill issue that the agent reports to
   the skill improvement log.

## Fast defaults (build with these; do not ask)

- **Cleaning:** drop the nulls, or impute the median.
- **Features:** an `nn.Embedding` for each categorical column, with
  `min(50, cardinality // 2 + 1)` dims (the cap limits memory for large
  vocabularies). Concatenate with standard-scaled numerics. No target
  encoding, no interactions, no aggregates: the embeddings are the feature
  work.
- **Model:** one fixed architecture, no search:
  `embeddings -> concat -> Linear(256) -> ReLU -> Dropout(0.1) -> Linear(64)
  -> ReLU -> Linear(1)`, `BCEWithLogitsLoss`, Adam `lr=2e-3`. Batch size
  2048 under ~1M rows, 8192 above.

## Eval rules (mandatory)

1. **Internal validation.** Before training, take 15% of the train rows
   (fixed seed) as validation. Fit the category vocabularies on the rest
   only. Map an unseen category to the code `0` ("unknown"). Use early
   stopping on the validation AUC (patience 3, max 25 epochs). Load the
   weights of the best validation epoch.
2. **Test once.** Score the test set exactly once, after step 1
   fixed the model. Never select an epoch or a checkpoint from the test
   AUC. A network's epoch loop can leak test information; a tree fit once
   cannot. (Measured: epoch chosen on test 0.7309; chosen on
   validation 0.7271. The leak was 0.004 AUC.)
3. **Sample.** For a sample of a large table, state its size in
   Requirements and Input as a bold percentage of the full source.

## Deliverable

`<project-folder>/monkey-mlp/report.md`, with the 7 sections of
monkey-mode's Deliverable (Requirements, Input, Design, Implementation,
Results, Learnings, Suggested Next Steps). Additions:
- Results: the selected validation epoch and its AUC, separate from the
  final test AUC. Say that the test set was scored exactly once.
- Learnings: if `monkey-mode/report.md` exists, compare with its metric
  in one line. Say if it is the same test set or only approximate
  (different sample or split).
- Requirements: mark each item "answered by user" or "self-inferred".

## Check

The background agent does "Check the output" in
`../ml-system-design/SKILL.md`. It does not ask the user, and it reports
each skill issue in its final message. Intent questions:
1. Do all 7 sections hold results of a real run?
2. Was the epoch selected on internal validation only, and was the test
   set scored exactly once?
3. Does each unseen category map to `0`, with vocabularies fit on the fit
   split only?
4. Is the comparison with monkey-mode labeled as same-test-set or
   approximate?

Done when the 4 answers are yes and `check_doc.py` prints `OK` for
`report.md` with:

```
--sections "Requirements,Input,Design,Implementation,Results,Learnings,Suggested Next Steps"
```
