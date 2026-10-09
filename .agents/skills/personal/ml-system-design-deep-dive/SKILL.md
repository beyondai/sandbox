---
name: ml-system-design-deep-dive
description: >-
  Use when writing or reviewing the Design Deep Dive section of an ML system
  design doc - data sources (online/offline, data engineering), feature list and
  feature engineering, candidate models and their tradeoffs, or training setup
  (loss function, algorithm, labeling, sampling). The paper alternative to the
  ml-modeling-* execution family, which answers the same questions hands-on -
  trigger on requests to pick a model, design features, specify training
  data/labels, or discuss model tradeoffs on paper.
---

# Design Deep Dive

The paper route after `design/high-level.md`. `ml-modeling-*` answers the
same 4 items by doing the work, and does not read this file.

Rules: `../ml-system-design/SKILL.md`, "Project folder", "Output docs",
"Check the output", "Skill improvement log".

## Modes

2 independent choices: Draft or Review, and Regular or Quick POC. The
keyword selects the speed (the list is in "Regular and Quick-POC mode" in
`../ml-system-design/SKILL.md`). Reason:
`../adr/0001-ml-modeling-family-and-continuity.md`.

- **Draft, Regular:** answer each item in the user's own numbers and
  words. Ask when a fact is unknown. Do not invent.
- **Draft, Quick POC (a one-hour MVP):** ask the essential questions for
  all 4 items in one batched round. Give a default for the rest, marked as
  an assumption. Target: a real but short answer to each item.
- **Review:** check that each item has a real answer. Report the gaps. Do
  not rewrite what is good.

## Steps

1. **Before the draft**, in one message (Quick POC: inside its one round):
   - State the problem in 1-3 sentences, and name the prediction targets.
     If there is no `prd/`, say so and offer `/ml-system-design-prd`
     first.
   - List the source files with row counts (a listing, not a profile).

   Wait for the user's answer.
2. **Draft the 4 items** (below).
3. **Write** `<project-folder>/design/deep-dive.md`, one heading for each
   item. `ml-system-design-delivery` uses it.
4. **Offer an ADR** for a Models or Training decision that is hard to
   reverse, would surprise a future reader, and was a real trade-off (the
   `domain-modeling` ADR criteria). Put it in
   `<project-folder>/adr/000N-*.md`.
5. **Check.**

## The 4 items

- **Data:** the sources for real-time inference and for batch training.
  The new data engineering work (for example an ETL job that joins 2
  logs).
- **Features:** a concrete list (user, item, context). Name each
  nontrivial transform (for example embeddings for a high-cardinality
  `user_id`).
- **Models:** the candidates, always with the simplest option that can
  work. The trade-offs: performance, running cost, maintenance cost,
  explainability. Select a model for each phase. A more complex candidate
  wins only if it passes the complexity gate: fill the cost table in
  `../ml-design-principles.md`, Principle 1. Name the architecture and why
  (shallow or deep; MLP, cross network, two-tower, or attention).
- **Training:** the loss, the algorithm, the source of the labels, and
  the sampling: class imbalance, and the negative sampling plan when the
  logs hold only positives (types, ratio, correction). The training
  setup: for a neural network the framework, optimizer, learning rate and
  schedule, batch size, epochs with early stopping, dropout and weight
  decay; for trees the key hyperparameters. Also the hardware (CPU or
  GPU) and the expected training time.

Starting values and the options for each choice:
`../ml-model-training.md`. Give rough values; mark each one as a starting
point to tune.

## Check

Do "Check the output" in `../ml-system-design/SKILL.md`. Intent questions:
1. Are the features named, not "relevant features"?
2. Are 2 or more candidates compared, with the simplest one included and
   a stated trade-off?
3. Does a complex choice have the cost table, and does it pass the gate?
4. Can the label source be traced to a real data pipeline? Does the loss
   match the PRD primary metric?
5. Does Training state the negative sampling plan (if the labels are
   implicit) and the training setup or tree hyperparameters, with the
   hardware and the time?

Done when the 5 answers are yes and `check_doc.py` prints `OK`.
