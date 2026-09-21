---
name: ml-system-design-definition
description: >-
  Use when writing or reviewing the Definition section of an ML system design
  doc — problem statement, requirements (features, out-of-scope,
  scale/latency/availability), success metrics (offline/online/guardrail), or
  team/stakeholders/dependencies for an ML system. Trigger on requests to write
  or check an ML design doc's problem statement, scope/out-of-scope list,
  non-functional requirements, offline vs online metrics, guardrail metrics, or
  stakeholder/dependency mapping.
---

# Definition

Project folder: see `../ml-system-design/SKILL.md`, "Which project folder".

Draft (Regular): answer each item below in the user's own numbers/words; ask if
unknown, never invent. Quick POC: state each item's most likely answer in one
pass, flagged as an assumption — mode by keyword ("poc"/"quick"/"mvp"/"fast" vs.
"regular"/nothing), see `../adr/0001-ml-modeling-family-and-continuity.md`.
Review: check each item is actually answered, not just headed; flag gaps, don't
rewrite what's solid.

- **Problem**: core problem, why now, user pain point, link to team/company
  goals.
- **Requirements — scope**: must-have features; explicit out-of-scope list for
  this version. Most-skipped item in review — check it first.
- **Requirements — non-functional**: expected load, latency (e.g. p99),
  availability target.
- **Metrics — offline**: static-dataset metrics (AUC, nDCG, precision/recall).
- **Metrics — online**: live A/B metrics (CTR, conversion, session time) plus
  guardrail metrics that must not regress.
- **Team**: stakeholders to inform, collaborating teams, blocking/blocked
  dependencies.
- **Team — reuse**: existing components reusable instead of rebuilt; downstream
  consumers of this system's output.

Done when every bullet above has a concrete answer in the doc, scaled to system
size — a small internal model doesn't need 10M req/min-grade detail, but
out-of-scope and the offline/online metric split are never optional.

If this run turns up a bug or a better design in this skill, or you ask for a
change to how it works, log it — see `../ml-system-design/SKILL.md`'s Skill
improvement log.
