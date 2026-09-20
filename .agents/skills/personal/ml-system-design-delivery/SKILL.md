---
name: ml-system-design-delivery
description: >-
  Use when writing or reviewing the Delivery section of an ML system design doc
  — execution timeline, deployment/rollout/testing strategy, A/B test and
  offline eval methodology, production monitoring, or fallback plans. Trigger on
  requests to design a rollout/ramp plan, an A/B test, a monitoring dashboard,
  or a fallback/kill-switch for an ML system going to production.
---

# Delivery

Draft (Regular): answer each item below in the user's own numbers/words; ask if
unknown, never invent. Quick POC: state each item's most likely answer in one
pass, flagged as an assumption — mode is chosen by keyword
("poc"/"quick"/"mvp"/"fast" vs. "regular"/nothing), see
`../adr/0001-ml-modeling-family-and-continuity.md`. Review: check each item is
actually answered, not just headed; flag gaps, don't rewrite what's solid.

- **Execution**: epics/milestones with dates; team process (e.g. sprint length,
  review cadence).
- **Deployment**: rollout plan (e.g. ramp %, schedule), testing plan
  (unit/integration/load), CI/CD strategy.
- **Eval**: A/B test design and significance method; offline eval methodology
  (e.g. held-out window). If this project forked into `ml-modeling-*`, reference
  the real `modeling/04-evaluate.md` results here instead of a hypothetical
  plan.
- **Monitoring**: system-health metrics (latency, error rate) and model-health
  metrics (prediction distribution, feature drift) on a live dashboard.
- **Fallback**: what happens when the new model/service fails or degrades —
  revert to prior model, or drop to a simple heuristic. Most-skipped item in
  review — check it first; a doc without one is incomplete.

Done when the rollout has a concrete ramp schedule, the fallback trigger and
target are both named, and monitoring lists specific metrics rather than "we'll
monitor performance."

## Offer an ADR

If the rollout or fallback strategy is hard to reverse, would surprise a future
reader, and was a real tradeoff, offer to record it in
`<project-folder>/adr/000N-*.md` rather than letting it live only in this doc.

If this run turns up a bug or a better design in this skill, or you ask for a
change to how it works, log it — see `../ml-system-design/SKILL.md`'s Skill
improvement log.
