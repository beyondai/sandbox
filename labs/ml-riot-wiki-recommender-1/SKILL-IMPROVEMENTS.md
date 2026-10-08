# Skill improvements - ml-riot-wiki-recommender-1

## 2026-10-08 - ml-system-design-monkey-mode
- **Source**: agent-found better design
- **Status**: proposed
- **Finding**: with no data referenced, the skill falls back to a synthetic
  dataset. For recommender and text tasks, synthetic text and behavior only
  replay what the generator encoded, so the baseline number is meaningless.
  This project used a public proxy instead (Wikipedia Clickstream, with real
  A->B transitions), and the results were informative.
- **Suggested change**: in "The 3 questions", item 1, replace the fallback
  with: "If no data is referenced, prefer a cited public proxy dataset with
  real labels of the same shape (e.g. clickstream for next-item
  recommendation, Stack Exchange PostLinks for related content). Fall back to
  synthetic data only for tabular tasks, or when no proxy fits in about 2 GB.
  State the proxy's distribution gap in Learnings."

## 2026-10-08 - ml-system-design-monkey-mode
- **Source**: user-requested
- **Status**: proposed
- **Finding**: the user asked for a click baseline plus an ML challenger. The
  skill's "one model, trained once" default conflicted with that, and the run
  had to override it ad hoc.
- **Suggested change**: in "Fast defaults", Model, add: "If the user asks for
  a baseline-vs-challenger comparison, build both (a non-learned baseline
  plus one model), and report the delta with a bootstrap CI against the
  success bar."

## 2026-10-08 - ml-system-design-monkey-mode
- **Source**: agent-found bug
- **Status**: proposed
- **Finding**: for ranking tasks scored with graded nDCG, the planned binary
  label (clicked or not) made the reranker unable to order candidates by
  volume. It scored -5.8% overall nDCG@10 against the click baseline, and
  head-bucket nDCG fell from 0.997 to 0.628. A regression on log1p(clicks)
  fixed it with no other change.
- **Suggested change**: in "Fast defaults", Model, add: "For ranking tasks
  scored with graded nDCG, train on the graded target (regression on log1p of
  the relevance, or LambdaMART), not a binary label."

## 2026-10-08 - ml-system-design-monkey-mode
- **Source**: agent-found bug
- **Status**: proposed
- **Finding**: Process step 3 tells the background agent to write
  `monkey-mode/report.md`. Claude Code blocks subagents from writing report
  files ("Subagents should return findings as text, not write report
  files"). The run finished, but `report.md` was missing. The main session
  had to save the returned text after the user approved. This happens on
  every run.
- **Suggested change**: in Process step 3, add: "The agent writes code,
  logs and metrics files itself. It does not write `report.md`. It returns
  the full `report.md` content as text in its final message." In step 4,
  replace "surface the results" with: "Save the returned text verbatim to
  `<project-folder>/monkey-mode/report.md`, check the format rules (80-column
  prose, no em dashes, all seven sections), then surface the results." In
  "Deliverable", change "Done when `report.md` exists" to "Done when the main
  session has saved `report.md`". Apply the same change to
  `ml-system-design-monkey-mlp` and to any other skill that has a subagent
  write a report file.
