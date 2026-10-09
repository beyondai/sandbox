# Skill improvements (all ml-* skills, all projects)

Contents: open entries from `labs/ml-riot-wiki-recommender-1`
(2026-10-09): train ranking path | train LightGBM check | evaluate ranking
metrics | serve bench --full | serving history cache | feature_selector
parquet | chain mode | spec refresh | gate per slice | age and traffic
slices | proxy data rule

The one shared log of proposed changes to the `ml-*` and `ml-critique*`
skills. Rules: `ml-system-design/SKILL.md`, "Skill improvement log".
Reasons: `adr/0004-skill-improvement-log.md`,
`adr/0016-shared-log-and-session-end-reflection.md`. Entries before
2026-10-09 stay in `labs/<project>/SKILL-IMPROVEMENTS.md` as history.

## 2026-10-09 - ml-modeling-train (ranking path)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found better design
- **Status**: adopted (2026-10-09): `ml-modeling-train`, "Ranking tasks";
  multiagent points to it (ADR 0017).
- **Finding**: the skill has no ranking path. The matrix, the threshold
  rule and the CV text assume one row per entity. For this recommender I
  had to add folds grouped by query, a per-query metric, and "no
  threshold" by hand (`modeling/train.py`).
- **Suggested change**: add a matrix row "Ranking (query, candidate)
  pairs | GBDT regression on the graded label | LambdaMART (listwise)".
  Under "Algorithm selection": "For ranking, use `GroupKFold` by the
  `dataset.group` column, score a per-query metric (nDCG@K), and save
  `threshold: None`. Train the simplest option as the PRD baseline rule
  scored on the same folds."

## 2026-10-09 - ml-modeling-train (LightGBM needs libomp)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found bug
- **Status**: adopted (2026-10-09): import check in `ml-modeling-train`,
  "Algorithm selection" (ADR 0017).
  Update: Homebrew can't install `libomp` on the user's Intel Mac (no
  bottle; source build failed); the dotfiles change was reverted, and the
  skill now says to use `HistGradientBoosting` on this machine.
- **Finding**: `uv add lightgbm` installs, but the import fails on macOS:
  the wheel needs the system `libomp`. The LambdaMART candidate could not
  run. XGBoost wheels have the same need.
- **Suggested change**: in `ml-model-training.md` (hardware notes) and
  the train skill: "Before a LightGBM or XGBoost candidate, run
  `uv run python3 -c 'import lightgbm'`. If it fails on `libomp`, the fix
  is a system install (this user: `homebrew.brews` in the nix-darwin
  config, then rebuild). Ask the user; don't install system libraries.
  Remove the package again if it can't load."

## 2026-10-09 - ml-modeling-evaluate (ranking metrics)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found better design
- **Status**: adopted (2026-10-09): `ml-modeling-evaluate`, "Ranking" (ADR
  0017).
- **Finding**: the skill has classification and regression templates
  only. A ranking evaluation needs a truth table, not only the candidate
  rows: nDCG over the candidates alone hid that 55% of new pages had no
  correct candidate. Item-side metrics found a real problem (the model
  showed new pages less often), which no query-side metric showed.
- **Suggested change**: add a "Ranking" section: nDCG@K with the ideal
  from the full truth (`dataset.truth_test`), recall@K, click-weighted
  recall, hit@K, coverage; candidate recall as the ceiling; per query
  slice weighted by the population, and per item slice; paired bootstrap
  over queries. Save per-row scores as parquet under `data/` when large
  (same rule as `ml-modeling-data`).

## 2026-10-09 - ml-modeling-serve (bench_serve.py in batch mode)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found bug
- **Status**: adopted (2026-10-09): `--full` and `--chunk` in `bench_serve.py`;
  serve skill "Measure" (ADR 0017).
- **Finding**: `bench_serve.py` times single rows and 1,000-row random
  batches. When `transform()` joins each call against a history table,
  every call pays a fixed cost: 1,789 rows/s in the 1,000-row batches,
  against 607,009 rows/s for one call over the whole test table. The
  script's batch number understated batch throughput by 340x.
- **Suggested change**: add `--full` to `bench_serve.py` (time one call
  over all rows, after a warm-up call) and `--chunk N`. In the skill:
  "In batch mode, report the `--full` throughput as `batch_rows_per_sec`;
  single-row latency only shows why the model stays off the request
  path."

## 2026-10-09 - ml-serving.md (cache history in the feature code)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found better design
- **Status**: declined as its own rule (2026-10-09): a coding detail; one
  sentence went into `ml-modeling-serve`, "serve.py".
- **Finding**: `features.py` read a 22M-row history table on every
  `transform()` call. Fine in training (one call), slow in serving (many
  calls). The fix was a per-process cache inside `features.py`, so serving
  still uses the training code.
- **Suggested change**: in "Online features": "If `transform()` loads
  history or lookup tables, cache them once per process inside the
  feature module (`functools.lru_cache`), not in `serve.py`. Then re-run
  the parity check: serving scores equal the evaluate scores."

## 2026-10-09 - ml-modeling scripts (feature_selector.py reads CSV only)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found bug
- **Status**: adopted (2026-10-09): parquet, `--sample`, `--drop` (ADR 0017).
- **Finding**: `feature_selector.py` takes only `--file <csv>`. The train
  table was 6.2M rows in parquet; I had to write a 200k-row CSV sample to
  the scratchpad first.
- **Suggested change**: accept `.parquet` (by extension) and add
  `--sample N` (seeded) and `--drop <cols>` for id columns.

## 2026-10-09 - ml-modeling (chain mode carries to later steps)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found better design
- **Status**: adopted (2026-10-09): `mode:` line in the spec; "Modes" in the
  router (ADR 0017).
- **Finding**: the mode is chosen by keyword in each request. The chain
  started in Quick POC, but `/ml-modeling-train` and later steps were run
  with no keyword, which means Regular by the rule. I kept Quick POC and
  said so; the skill does not say which is right.
- **Suggested change**: the first step writes `mode: quick-poc|regular`
  as line 3 of `spec/<topic>.md`. Each later step uses it unless the
  request has a mode keyword, and records the mode it used.

## 2026-10-09 - ml-modeling (hash refresh left the spec stale)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found bug
- **Status**: adopted (2026-10-09): router, "Design docs changed?" step 5 and
  "Closing the loop" (ADR 0017).
- **Finding**: `design/high-level.md` renamed the "cold" slice to "new"
  and the hash in the spec was refreshed, but the spec's gate line still
  said "cold and long-tail" until the train step found it. A hash refresh
  says "seen", not "applied".
- **Suggested change**: in "Design docs changed?": "Before you refresh a
  hash, diff the changed file and update every spec line that cites the
  changed content (renamed terms, changed gates or metrics). Then
  refresh."

## 2026-10-09 - ml-system-design-high-level (gate per segment)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: user-requested
- **Status**: declined (2026-10-09): fits products with clear segments; stays a
  Riot wiki project decision (`adr/0002` there).
- **Finding**: the V1 gate was all-or-nothing over two slices, and its
  fallback covered only one failure shape. The user changed it to
  per-slice routing (the model ranks only the slices where it wins with a
  CI above 0) plus an item-side guardrail for new pages.
- **Suggested change**: in Phasing: "When the PRD defines slices, state
  the complexity gate per slice: the model serves a slice only where it
  passes; the baseline serves the rest. For recommenders, add an
  item-side guardrail (new items are not shown less often than by the
  baseline)." Add the same line to `ml-design-principles.md`, Principle 1.

## 2026-10-09 - ml-playbooks.md and ml-system-design-definition (slices)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: user-requested
- **Status**: declined (2026-10-09): a recommender default, not general; stays
  in the Riot wiki PRD.
- **Finding**: the PRD first had one "cold" slice. The user separated
  cold-start (new: no time to learn yet) from long-tail (rarely used,
  even when old), on both the query side and the item side. The data
  confirmed they fail differently (candidate recall 0.19 new, 0.04
  dormant, 0.73 long-tail).
- **Suggested change**: in the recommendations playbook and the
  Definition "Metrics - offline" bullet: "Slice by age (new) and by
  traffic (dormant, long-tail, torso, head), separately, on the query
  side and the item side. Use percentiles until the scale is known."

## 2026-10-09 - ml-modeling and ml-system-design (proxy data rule)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: user-requested
- **Status**: adopted (2026-10-09): router, "Proxy data" (ADR 0017).
- **Finding**: the user said the Wikipedia data is only a proxy, and every
  design suggestion must still be for the Riot wiki. The skills have no
  rule for proxy data; this lives only in project memory.
- **Suggested change**: in the `ml-modeling` router: "When the data is a
  proxy for the target system, each finding in `0N-*.md` gets a 'For
  <target>' line with the design input. Proxy numbers are evidence or a
  lower bound, never the target's numbers. Name the signals the proxy
  lacks."

## 2026-10-09 - ml-critique (Normal mode covers every design step)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: user-requested
- **Status**: adopted (2026-10-09): ADR 0018.
- **Finding**: the user wants Normal mode to check every key decision and
  step of the ml-system-design and ml-modeling skills. A comparison found
  items with no catalog check: definition Team (stakeholders,
  dependencies, reuse), the baseline parts (status quo, floor, build
  decision), the deep-dive feature list, the delivery test plan, CI/CD
  and execution, post-delivery Democratize, the data profile, proxy
  data, ranking evaluation against the full truth, and serving mode and
  cost. No map shows which skill item each check covers.
- **Suggested change**: add `ml-critique/references/coverage.md` (each
  skill checklist item -> catalog IDs). Add system C7, G0, G1a, I10, I11,
  J6 and modeling B8, B9, I11, K5. Mark modeling I8 `[C]`.

## 2026-10-09 - ml-critique (importance order has no single sort key)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found bug
- **Status**: adopted (2026-10-09): ADR 0018.
- **Finding**: "Priority" rule 1 (upstream first) has no scope, and rule 2
  says "inside one priority". A reader can put an upstream P2 before a
  downstream P1. The checks inside a catalog section have no order.
  "Done well" has no order rule.
- **Suggested change**: one sort key: priority, then upstream, then
  effect, then confidence. Order the checks in each section from the
  most likely P1. Order strengths by the cost to lose them.

## 2026-10-09 - ml-critique (Quick mode replaces Brief, 2-hour budget)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: user-requested
- **Status**: adopted (2026-10-09): ADR 0018.
- **Finding**: the user wants a quick mode that limits the whole critique
  (select to document) to 2 hours at most. It checks the most important
  topics first and is not complete. Brief limits only the checks and the
  presentation, to 45 minutes.
- **Suggested change**: rename Brief to Quick. Checks in importance order
  until the critique budget is used. Add "Appendix" (found, not
  presented) and "Not checked" (skipped for time) sections.

## 2026-10-09 - ml-critique (critique context)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: user-requested
- **Status**: adopted (2026-10-09): ADR 0018.
- **Finding**: a critique can have a purpose with its own demands (for
  example a Riot interview with required topics and a time limit). The
  skill has no place for it.
- **Suggested change**: ask for a critique context in Select. The
  general rules apply; the context wins only on a conflict. Note each
  conflict in chat and in a "Context" section. No context: general
  rules.

## 2026-10-09 - ml-critique (ask fresh or reference view every time)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: user-requested
- **Status**: adopted (2026-10-09): ADR 0018.
- **Finding**: Select asks about a reference design with the default
  "no". The user wants to choose fresh or with-my-design on each run.
- **Suggested change**: Select asks mode, view, and context in one
  message, with no default for view and context, and waits for the
  answers.

## 2026-10-09 - ml-critique (one mixed file gets both lenses)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found bug
- **Status**: adopted (2026-10-09): ADR 0018.
- **Finding**: the lens is selected by folder (`prd/` or `spec/`). A single
  report with design and results content (the Riot interview report) has
  no rule.
- **Suggested change**: for one file, select the lens by its sections;
  both kinds of content get both lenses.

## 2026-10-09 - ml-playbooks.md (item-to-item recommendation)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found better design
- **Status**: adopted (2026-10-09): ADR 0018.
- **Finding**: the Recommendation playbook assumes user-to-item ranking
  with impressions. A "related items" recommender (the Riot interview
  report) gets no check that the trained model beats its untrained
  content similarity, or that the evaluation ranks the full catalog.
- **Suggested change**: add an item-to-item variant to Recommendation:
  baseline, classic mistakes, and questions.
