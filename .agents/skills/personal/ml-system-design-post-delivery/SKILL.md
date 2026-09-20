---
name: ml-system-design-post-delivery
description: Use when writing or reviewing the Post-Delivery section of an ML system design doc — post-launch result analysis, model explainability (SHAP/LIME), the next-iteration roadmap, or democratizing/reusing ML components across teams. Trigger on requests to plan A/B test result analysis, add model explainability, sketch a V2/V3 roadmap, or identify what an ML system's components let other teams reuse.
---

# Post Delivery

Draft (Regular): answer each item below in the user's own numbers/words; ask if unknown, never invent. Quick POC: state each item's most likely answer in one pass, flagged as an assumption — mode by keyword ("poc"/"quick"/"mvp"/"fast" vs. "regular"/nothing), see `../adr/0001-ml-modeling-family-and-continuity.md`. Review: check each item is actually answered, not just headed; flag gaps, don't rewrite what's solid.

- **Analysis**: plan for the post-A/B deep-dive — not just what happened, but why.
- **Explainability**: how model decisions become human-understandable (e.g. SHAP, LIME) — for debugging and stakeholder trust.
- **Iteration**: forward roadmap (V2, V3, ...) based on the analysis plan above.
- **Democratize**: specific components (features, model architecture, platform pieces) other teams could reuse — name the team and the component, not "this could help others."

Done when Democratize names an actual team + component rather than staying generic, and Iteration lists concrete next-version items rather than "TBD based on results."
