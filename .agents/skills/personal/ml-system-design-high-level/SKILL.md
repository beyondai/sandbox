---
name: ml-system-design-high-level
description: >-
  Use when writing or reviewing the High-level Design section of an ML system
  design doc — ML problem framing, the online-inference/offline-training
  architecture diagrams, or crawl-walk-run delivery phasing (V0/V1/V2). Trigger
  on requests to frame a business problem as an ML problem, design an ML
  pipeline architecture, or phase an ML project into milestones.
---

# High-level Design

Project folder and output format: see `../ml-system-design/SKILL.md`,
"Which project folder" and "Output docs".

Draft (Regular): answer each item below in the user's own numbers/words; ask if
unknown, never invent. Quick POC: state each item's most likely answer in one
pass, flagged as an assumption — mode is chosen by keyword
("poc"/"quick"/"mvp"/"fast" vs. "regular"/nothing), see
`../adr/0001-ml-modeling-family-and-continuity.md`. Review: check each item is
actually answered, not just headed; flag gaps, don't rewrite what's solid.

- **ML framing**: restate the business problem as a precise ML problem (e.g.
  "show better content" → "predict per-item click probability,
  learning-to-rank"). This is the fork point into `ml-modeling-*`, so the one
  sentence must be backed by, per model: prediction target; label definition
  and horizon; scoring population and cadence (who gets a score, when); unit
  of prediction (what one row is); known exclusions or contamination (e.g.
  players in a past campaign). If the framing yields more than one model, add
  one line "This folder builds: <model>" — one model per project folder; the
  others get their own. The primary metric stays in the PRD; reference it.
- **Architecture**: two diagrams, not one — online inference (real-time
  request/response path) and offline training (named source tables/logs →
  processing → model training). Conflating them is the most common review
  flag here. Name the concrete sources; "user data" is not a source.
- **Phasing**: crawl-walk-run sequence (V0/V1/V2). Per phase: features shipped,
  model class (baseline / first real model / stretch), rough timeline,
  headcount.

Done when the ML framing is one precise sentence backed by target, label +
horizon, population, unit, and exclusions per model, both diagrams exist
separately with the offline one naming its sources, and every phase names
features + model class + timeline + headcount rather than just a version
number.

## Write the file

Write the settled answers to `<project-folder>/design/high-level.md`, one
heading per item above (ML framing, Architecture, Phasing). Create `design/`
if it doesn't exist. Diagrams are ASCII in fenced code blocks, matching the
rest of this repo's design docs. The ADR below is for one hard-to-reverse
decision, not a home for this whole section.

This file is the fork point: after it, the project goes either to
`ml-system-design-deep-dive` (the paper deep dive) or to `ml-modeling-*` (the
hands-on one), and both lead to `ml-system-design-delivery`. See the
`ml-modeling` router for what it reads from here.

## Offer an ADR

If the architecture choice is hard to reverse, would surprise a future reader,
and was a real tradeoff (not the only reasonable option), offer to record it in
`<project-folder>/adr/000N-*.md` rather than letting it live only in this doc.

If this run turns up a bug or a better design in this skill, or you ask for a
change to how it works, log it — see `../ml-system-design/SKILL.md`'s Skill
improvement log.
