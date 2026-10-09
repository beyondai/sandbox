---
name: ml-system-design-post-delivery
description: >-
  Use when writing or reviewing the Post-Delivery section of an ML system design
  doc - post-launch result analysis, model explainability (SHAP/LIME), the
  next-iteration roadmap, or democratizing/reusing ML components across teams.
  Trigger on requests to plan A/B test result analysis, add model
  explainability, sketch a V2/V3 roadmap, or identify what an ML system's
  components let other teams reuse.
---

# Post Delivery

Writes `<project-folder>/design/post-delivery.md`, one heading for each
item.

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

- **Analysis:** the plan for the analysis after the A/B test: why it
  happened, not only what happened.
- **Explainability:** how model decisions become clear to people (for
  example SHAP, LIME), for debugging and stakeholder trust.
- **Iteration:** the roadmap (V2, V3, ...), based on the analysis plan.
- **Democratize:** the components (features, model architecture, platform
  parts) that other teams can reuse. Name the team and the component.

## Check

Do "Check the output" in `../ml-system-design/SKILL.md`. Intent questions:
1. Does the analysis plan look for causes and segments, not only the
   headline result?
2. Does Iteration list concrete next-version items, not "TBD based on
   results"?
3. Does Democratize name a real team and a real component?

Done when the 3 answers are yes and `check_doc.py` prints `OK`.
