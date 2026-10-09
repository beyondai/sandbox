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
- **Status**: declined (replaced by the 2026-10-08 entry "Baseline as a
  design decision" below)
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

## 2026-10-08 - ml-system-design-monkey-mode
- **Source**: user-requested
- **Status**: adopted (2026-10-08, as a new "Saved outputs" section in
  the monkey-mode SKILL.md; monkey-mlp and ml-modeling-evaluate not yet)
- **Finding**: the run saved only final metrics. When the PRD changed the
  cutoff from @10 to @5, the full pipeline (data prep, training, scoring) had
  to run again to recompute metrics. Eval changes should only re-run eval.
- **Suggested change**: in "Deliverable", add: "Save intermediate data and
  per-query model outputs under the gitignored data folder (parquet): the
  prepared and split data, the candidate sets, and each model's scores for
  its top 50 items per query. Split the code into two entry points: `train`
  (prepare, fit, score, save) and `eval` (read the saved outputs, compute
  metrics at any K, write the metrics file). A metric or cutoff change runs
  `eval` only." Apply the same rule to `ml-system-design-monkey-mlp` and the
  `ml-modeling-*` evaluate step.

## 2026-10-08 - ml-system-design-definition (Baseline as a design decision)
- **Source**: user-requested
- **Status**: adopted (2026-10-08)
- **Finding**: no skill called out a simple, often non-ML baseline early in
  the design. Baselines appeared only at the end (`ml-modeling-evaluate`,
  majority class or mean only, nothing for ranking) or in the critique
  playbooks. The user wants the baseline named at the PRD stage, with a
  recommendation, even if it is never built.
- **Change applied**:
  - `ml-system-design-definition`: new checklist bullet "Baseline" (status
    quo, recommended baseline from the playbook, floor, build decision).
    Never skipped, like out-of-scope.
  - `ml-system-design-high-level`: Phasing V0 is the PRD baseline, or says
    why not. Later phases state their gain over it.
  - `ml-system-design-delivery`: the default fallback heuristic is the PRD
    baseline.
  - `ml-modeling-evaluate`: compare against the PRD baseline if built,
    else its floor, and say so.
  - `ml-system-design`: the never-skip list is now out-of-scope, baseline
    and fallback.
  - `ml-critique/references/playbooks.md` moved to the shared
    `ml-playbooks.md`. The 3 critique skills point to the new path.
    `adr/0009-ml-critique-skills.md` keeps the old path as history.
  - Monkey mode is unchanged. It stays a separate track.

## 2026-10-08 - ml-modeling-data
- **Source**: agent-found better design
- **Status**: proposed
- **Finding**: The skill writes the labeled table as
  `modeling/datasets/<task>_{train,test}.csv` inside the project folder. For
  large tables (here 8.6M pair rows) CSV is slow and large. It also clashes
  with the monkey-mode rule that generated data goes under the sandbox-root
  `data/<dataset>/`. The skill also assumes one row per entity. A ranking
  task needs a group id (the query) and a separate truth table for recall.
- **Suggested change**: In "Build or register the labeled table", allow
  parquet under `<sandbox>/data/<dataset>/modeling/` for tables over about
  1M rows, check each path with `git check-ignore`, and record the paths in
  the `dataset` block. Add optional `group` and `truth_train`/`truth_test`
  keys to the `dataset` schema for ranking tasks.
- **Finding 2**: `dashboard/.port` and `dashboard/.pid` are not git-ignored
  by the sandbox `.gitignore`, so they show up as untracked files.
- **Suggested change 2**: Ask the user once to add `dashboard/.port` and
  `dashboard/.pid` to `.gitignore`, or write them under `data/`.

## 2026-10-09 - ml-modeling-features
- **Source**: user-requested
- **Status**: proposed
- **Finding**: In a POC on a proxy dataset, the skill lists text and
  embeddings under "not used" with no further record. For the Riot wiki
  project, text and embeddings are core to the real use case (new pages,
  near-duplicates), even though the proxy has no text. The user asked to
  keep them in the discussion.
- **Suggested change**: In "Embeddings" and "Cheap text signals", add:
  when the target use case needs text or embedding features that the POC
  data can't supply, keep them in `02-features.md` as a "not built"
  design section (features, reason, cost, model choice, how to test), and
  point to a feasibility note for getting the data. Never list them as
  dropped.
