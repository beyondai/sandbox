---
name: ml-system-design-high-level
description: >-
  Use when writing or reviewing the High-level Design section of an ML system
  design doc - ML problem framing, the online-inference/offline-training
  architecture diagrams, or crawl-walk-run delivery phasing (V0/V1/V2). Trigger
  on requests to frame a business problem as an ML problem, design an ML
  pipeline architecture, or phase an ML project into milestones.
---

# High-level Design

Rules: `../ml-system-design/SKILL.md`, "Project folder", "Output docs",
"Check the output", "Skill improvement log".

## Modes

- **Regular draft:** answer each item in the user's own numbers and
  words. Ask when a fact is unknown. Do not invent.
- **Quick POC draft** (keywords: "Regular and Quick-POC mode" in
  `../ml-system-design/SKILL.md`): give the most
  likely answer to each item in one pass, marked as an assumption.
- **Review:** check that each item has a real answer. Report the gaps. Do
  not rewrite what is good.

## Checklist

- **ML framing.** State the business problem as a precise ML problem (for
  example "show better content" -> "predict per-item click probability,
  learning-to-rank"). This is the fork point into `ml-modeling-*`. For
  each model, give:
  - the prediction target;
  - the label definition and horizon;
  - the scoring population and cadence (who gets a score, and when);
  - the unit of prediction (what one row is);
  - the known exclusions or contamination (for example players in a past
    campaign).

  For more than one model, add "This folder builds: <model>". One model
  for each project folder. Refer to the primary metric in the PRD; do not
  repeat it.
- **Architecture.** 2 separate diagrams:
  - online inference (the request/response path), or for a batch-only
    system the scoring and delivery path (scheduled job -> scores ->
    consumer);
  - offline training (named source tables or logs -> processing ->
    training).

  One diagram for both is the most common review finding. Name the real
  sources: "user data" is not a source.
- **Phasing.** V0, V1, V2 (crawl, walk, run). For each phase: the
  features, the model class and its architecture family (for example
  GBDT, then two-tower retrieval + DCN-v2 ranker; options in
  `../ml-model-training.md`), the timeline, and the headcount.
  - V0 is the PRD's recommended baseline (Definition, "Baseline"), or the
    doc says why not.
  - Each later phase names its expected gain over the baseline: the gain
    that pays for the added complexity (`../ml-design-principles.md`,
    Principle 1).

## Write the file

Write `<project-folder>/design/high-level.md`, with one heading for each
item: ML framing, Architecture, Phasing. Draw the diagrams as ASCII in
fenced code blocks.

After this file, the project goes to `ml-system-design-deep-dive` (paper)
or to `ml-modeling-*` (hands-on). Both lead to `ml-system-design-delivery`.
`../ml-modeling/SKILL.md`, "Required upstream", lists what modeling reads
from here.

## Offer an ADR

Offer an ADR in `<project-folder>/adr/000N-*.md` for an architecture
choice that is hard to reverse, would surprise a future reader, and was a
real trade-off. The ADR holds one decision, not this section.

## Check

Do "Check the output" in `../ml-system-design/SKILL.md`. Intent questions:
1. Is the framing one precise sentence, with the target, label and
   horizon, population, unit, and exclusions for each model?
2. Does the label horizon cover the decision window (for an action: the
   time that it needs to have an effect)? Does the framing name any
   feedback from the action on future labels?
3. Are there 2 separate diagrams, and does the offline one name its
   sources?
4. Is V0 the simplest option that can ship? Does each phase give
   features, model class, timeline, headcount, and its expected gain?

Done when the 4 answers are yes and `check_doc.py` prints `OK`.
