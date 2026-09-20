---
name: ml-system-design-deep-dive
description: Use when writing or reviewing the Design Deep Dive section of an ML system design doc — data sources (online/offline, data engineering), feature list and feature engineering, candidate models and their tradeoffs, or training setup (loss function, algorithm, labeling, sampling). Also the required upstream step for the ml-modeling-* execution family — trigger on requests to pick a model, design features, specify training data/labels, discuss model tradeoffs, or start a quick ML POC/MVP.
---

# Design Deep Dive

Two axes, independent of each other: Draft vs. Review (what you're doing), and
Regular vs. Quick-POC (how fast). Mode is chosen by keyword in the request —
"poc"/"quick"/"mvp"/"prototype"/"fast"/"one hour" → Quick POC;
"regular"/"full"/nothing → Regular (default). Full rationale in
`../adr/0001-ml-modeling-family-and-continuity.md`.

**Draft, Regular**: answer each item below in the user's own numbers/words; ask
if unknown, never invent.

**Draft, Quick POC — a one-hour MVP**: ask the essential questions from the four
items below in one batched round, not sequential grilling; state a reasonable
default for anything not essential and flag it as an assumption. Target: a real
but surface-level answer to all four items, fast — this file is what unblocks
`ml-modeling-*`, so it needs to exist quickly, not be exhaustive.

**Review** (either mode): check each item is actually answered, not just headed;
flag gaps, don't rewrite what's solid.

- **Data**: sources feeding real-time inference vs. batch training; new data
  engineering work needed (e.g. an ETL pipeline joining two logs).
- **Features**: concrete feature list (user, item, contextual); nontrivial
  feature engineering called out (e.g. embeddings for high-cardinality
  `user_id`).
- **Models**: candidate model types considered; tradeoffs between them
  (performance vs. training cost vs. interpretability); chosen model justified
  per phase, not just for the final version.
- **Training**: loss function optimized; training algorithm; source of
  ground-truth labels; sampling strategy if needed (e.g. class imbalance).

Done when features are named (not "we'll use relevant features"), at least two
model candidates are compared with a stated tradeoff, and the label source is
traceable to a real data pipeline.

## Write the file

Write the settled answers to `<project-folder>/design/deep-dive.md`, one heading
per item above — this is what `ml-modeling-*` reads to continue into execution,
in both modes. Create `design/` if it doesn't exist.

## Offer an ADR

If a Models or Training decision is hard to reverse, would surprise a future
reader, and was a real tradeoff (not the only reasonable option) — all three,
per `domain-modeling`'s ADR criteria — offer to record it in
`<project-folder>/adr/000N-*.md` rather than letting it live only in this file.

If this run turns up a bug or a better design in this skill, or you ask for a
change to how it works, log it — see `../ml-system-design/SKILL.md`'s Skill
improvement log.
