---
name: ml-system-design-definition
description: >-
  Use when writing or reviewing the Definition section of an ML system design
  doc - problem statement, requirements (features, out-of-scope,
  scale/latency/availability), success metrics (offline/online/guardrail,
  intended behavior), or team/stakeholders/dependencies for an ML system.
  Trigger on requests to write or check an ML design doc's problem statement,
  scope/out-of-scope list, non-functional requirements, offline vs online
  metrics, guardrail metrics, ways a model can game its metric, or
  stakeholder/dependency mapping.
---

# Definition

Rules: `../ml-system-design/SKILL.md`, "Project folder", "Output docs",
"Check the output", "Skill improvement log".

Writes `<project-folder>/design/definition.md`, one heading for each checklist
item. Use this skill for a project without a PRD, or to review a Definition. A
project with `prd/<topic>.md` does not draft this section: the PRD is the
Definition. When `ml-system-design-prd` calls this skill, the POC draft becomes
grilling rounds, and nothing is written to `design/`.

## Modes

- **Regular draft:** answer each item in the user's own numbers and
  words. Ask when a fact is unknown. Do not invent.
- **Quick POC draft** (keywords: "Regular and Quick-POC mode" in
  `../ml-system-design/SKILL.md`): give the most
  likely answer to each item in one pass, marked as an assumption.
- **Review:** check that each item has a real answer, not only a heading.
  Report the gaps. Do not rewrite what is good.

## Checklist

- **Problem:** the core problem, why now, the user pain point, the link
  to team or company goals, and the event to predict in business terms
  (what happens, to whom, by when). Metric thresholds depend on it;
  high-level gives the exact label and horizon.
- **Requirements, scope:** the must-have features, and an explicit
  out-of-scope list for this version. Reviews skip this item most often:
  check it first.
- **Requirements, non-functional:** peak load (QPS, not the average:
  serving capacity is sized for it), latency (for example p99),
  availability, the explainability need (hard or soft), and the cost
  sensitivity. A level (`low`/`medium`/`high`) or `unknown` is a valid
  cost answer. See `../ml-design-principles.md`, Principle 1.
- **Baseline:** the simple approach that the ML system must beat. It is
  often not ML. It is a design decision: the build can wait.
  - **Status quo:** what users do today without the system.
  - **Recommended baseline:** the strong simple baseline from the problem
    type's playbook (`../ml-playbooks.md`, part 3, "Baseline"). Examples:
    click popularity or co-occurrence for search and recommendation, a
    recency rule for churn, seasonal naive for forecasting. Recommend one.
    If no playbook fits, use the closest one and say so, or state the
    domain rule that people use today.
  - **Floor:** the most naive version (random, majority class, mean
    prediction, global popularity). It shows if the metric means anything.
  - **Build decision:** now, later, or never.
- **Metrics, offline:** metrics on a static dataset (AUC, nDCG,
  precision/recall).
- **Metrics, online:** live A/B metrics (CTR, conversion, session time),
  and guardrail metrics that must not get worse.
- **Metrics, intended behavior:** one or two lines on what the model must
  do in user terms, and the ways the model can game the primary metric
  (for example the same popular items for all users), each with a
  guardrail. If the goal is a target level, not a maximum, say so. See
  `../ml-design-principles.md`, Principle 2.
- **Team:** stakeholders to inform, collaborating teams, blocking and
  blocked dependencies.
- **Team, reuse:** existing components to reuse, and the downstream
  consumers of the output.

Scale the depth to the system size. Out-of-scope, the baseline, and the
offline/online metric split are always required.

## Check

Do "Check the output" in `../ml-system-design/SKILL.md`. Intent questions:
1. Does each bullet have a concrete answer, not only a heading?
2. Does the problem name the decision that the model controls?
3. Is there one primary offline metric, with a threshold? Does it connect
   to the online metric? Does each way to game it have a guardrail?
4. Is the out-of-scope list specific? Does the baseline section recommend
   one baseline?

Done when the 4 answers are yes and `check_doc.py` prints `OK`.
