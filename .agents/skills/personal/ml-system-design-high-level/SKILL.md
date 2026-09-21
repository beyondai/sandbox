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

Draft (Regular): answer each item below in the user's own numbers/words; ask if
unknown, never invent. Quick POC: state each item's most likely answer in one
pass, flagged as an assumption — mode is chosen by keyword
("poc"/"quick"/"mvp"/"fast" vs. "regular"/nothing), see
`../adr/0001-ml-modeling-family-and-continuity.md`. Review: check each item is
actually answered, not just headed; flag gaps, don't rewrite what's solid.

- **ML framing**: restate the business problem as a precise ML problem (e.g.
  "show better content" → "predict per-item click probability,
  learning-to-rank").
- **Architecture**: two diagrams, not one — online inference (real-time
  request/response path) and offline training (data processing → model
  training). Conflating them is the most common review flag here.
- **Phasing**: crawl-walk-run sequence (V0/V1/V2). Per phase: features shipped,
  rough timeline, headcount.

Done when the ML framing is one precise sentence (not a restated business goal),
both diagrams exist separately, and every phase names features + timeline +
headcount rather than just a version number.

## Write the file

Write the settled answers to `<project-folder>/design/high-level.md`, one
heading per item above (ML framing, Architecture, Phasing). Create `design/`
if it doesn't exist. Diagrams are ASCII in fenced code blocks, matching the
rest of this repo's design docs. The ADR below is for one hard-to-reverse
decision, not a home for this whole section.

## Offer an ADR

If the architecture choice is hard to reverse, would surprise a future reader,
and was a real tradeoff (not the only reasonable option), offer to record it in
`<project-folder>/adr/000N-*.md` rather than letting it live only in this doc.

If this run turns up a bug or a better design in this skill, or you ask for a
change to how it works, log it — see `../ml-system-design/SKILL.md`'s Skill
improvement log.
