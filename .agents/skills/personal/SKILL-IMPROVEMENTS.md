# Skill improvements (all ml-* skills, all projects)

Contents: open entries from `labs/ml-riot-wiki-recommender-1`
(2026-10-09): train ranking path | train LightGBM check | evaluate ranking
metrics | serve bench --full | serving history cache | feature_selector
parquet | chain mode | spec refresh | gate per slice | age and traffic
slices | proxy data rule | critique time
estimates | tag user findings | Done well filter | share-out and merge
| effect is a failure | question order | share-out screen
skills | skill-check fixes | intended behavior and change cadence |
no top-3 cap | context for the share-out | requirements and cost is P1 |
Principle 2 skill-check fixes | Principle 3 and Retraining item |
merge of a merge | disagreement labels | sources under old rules |
share-out open choices at write

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

## 2026-10-09 - ml-critique lenses (output exposure filters)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found gap (both lenses, Quick run on the interview report)
- **Status**: modified and adopted (2026-10-09): not a catalog item. One classic
  mistake each in `ml-playbooks.md`, Search ranking and RAG (ADR 0019).
  Reason: both lenses found it through the Recommendation playbook.
- **Finding**: neither catalog checks what the served items expose. System
  C6 covers only PII in features. Modeling K4 and K5 cover latency, mode,
  and cost. The permission filter, "exclude the query item", dedup, and
  status filters appear only in the item-to-item playbook, so other
  recommenders and search designs miss them.
- **Suggested change**: add one catalog item to each lens: "Served
  output filters: access rights per viewer, the query item, near
  duplicates, archived or stale items. Retrieve more than K, then filter."

## 2026-10-09 - ml-critique-modeling (sampled-ratio floor)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found gap
- **Status**: declined (2026-10-09): both lenses found the 0.80 floor with the
  current G0 check. No failure observed (ADR 0019).
- **Finding**: the catalog does not tell the reviewer to compare accuracy
  or AUC with the trivial floor at the sampled negative ratio. At 1:4, a
  constant "0" gets accuracy 0.80. There is also no item for "the author
  dismisses or misreads the one metric that matches the product".
- **Suggested change**: in I1 (or G0), add: "With sampled negatives,
  state the constant-prediction floor at that ratio." Add I12: "Does the
  write-up read each metric correctly, and does it act on the metric that
  matches the product?"

## 2026-10-09 - ml-critique lenses (text-only hybrid report)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found gap
- **Status**: adopted (2026-10-09), reopened: the next run met the unblock
  condition (the lenses gave P1 vs P2 for 2 findings). `ml-critique` step
  2.1, both lens Evidence sections (ADR 0020). Earlier: deferred (ADR 0019).
- **Finding**: the modeling lens step 1 and its Evidence rules assume a
  project folder with code and probe output. A text-only report (the
  common interview case) has no rule. Both lenses also had no rule to
  divide a mixed report, so they duplicated the split, metric, loss, and
  filter findings.
- **Suggested change**: in both lenses: "Text-only write-up: evidence is
  `file:line`; probes are arithmetic only." In ml-critique step 2: "When
  both lenses run on one file, tell each lens its owned sections. The
  merge joins the overlap."

## 2026-10-09 - ml-critique-system (index version at retrain)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found gap
- **Status**: declined (2026-10-09): narrow (embedding retrieval only), and the
  system lens found it anyway (ADR 0019).
- **Finding**: F5 and F6 cover model versions, not the embedding index. A
  weekly retrain (and a TF-IDF vocabulary refit) changes the embedding
  space. A partial index update mixes 2 incompatible spaces.
- **Suggested change**: add to F6: "Version the model and its index
  together, swap the index atomically, keep the previous pair for
  rollback, and gate promotion on the offline metric."

## 2026-10-09 - ml-critique-modeling (two sources for the Quick budget)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found bug
- **Status**: declined (2026-10-09): housekeeping, no effect on a finding.
  Fix it in passing at the next edit of that file (ADR 0019).
- **Finding**: the lens SKILL.md hardcodes the Quick budget (40 minutes).
  The router also passes the budget. A context time limit that scales the
  budget then conflicts with the lens text.
- **Suggested change**: the lens says "use the budget that the router
  gives" and removes the number.

## 2026-10-09 - ml-critique (question format)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: user feedback (confirmed approach)
- **Status**: adopted (2026-10-09): `ml-critique` step 2 part 4, both
  lenses step 5 and Check (ADR 0019).
- **Finding**: part 4 gives a question and an expected answer only. The
  user did not see why "What share of positives are on-page link
  clicks?" mattered until it was expanded: what the question means (a
  small path diagram), why it matters (3-4 effects), and a table of the
  action for each answer. The user said this part was "very good" and
  new to them. Ambiguous author claims ("recommendations are
  subjective") also need a split into their possible meanings.
- **Suggested change**: in ml-critique step 2 part 4 and both lenses,
  each question gets: the question, the expected answer, why it matters
  (one line), and what each likely answer changes. For a vague claim in
  the write-up, ask "in which sense?" and list the meanings with the fix
  for each.

## 2026-10-09 - ml-critique (several versions of one critique)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: user-requested
- **Status**: declined (2026-10-09): low value; add `-v<N>` by hand when a file
  exists (ADR 0019).
- **Finding**: the user runs several critique versions of one write-up
  on the same day, then researches across them. The name
  `critique/<date>-<lens>.md` collides. Also, the user stopped Converge
  early ("no need to prioritize now, just note the priorities") to save
  a version. The skill has no "save this version" exit.
- **Suggested change**: name the file `<date>-<lens>-v<N>.md` when one
  exists. Add a Converge exit: "save version". Accepted items are
  recorded, open items go to Deferred ("compare versions first"), and
  the priorities stay as noted.

## 2026-10-09 - ml-system-design and ml-critique (log filter)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: user-requested
- **Status**: adopted (2026-10-09): `ml-system-design`, "Skill
  improvement log"; `ml-critique` step 2.3; both lens Checks (ADR 0019).
- **Finding**: the lens subagents were asked to report skill issues, so
  each one returned some. 6 of 7 entries from the interview critique
  showed no failure: the lenses found those problems anyway. The user
  saw only 1 entry as an obvious improvement.
- **Suggested change**: log an agent-found entry only with evidence that
  the skill made the work worse (a missed, wrong, or late result, or
  extra work for the user). The lenses return an issue only under the
  same rule.

## 2026-10-09 - ml-critique (time estimates are human time, not agent time)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: user-requested
- **Status**: modified and adopted (2026-10-09): Quick mode is removed,
  not redefined. Each run checks the full catalog; the share-out limit is
  handled by `ml-critique-share-out` (ADR 0020).
- **Finding**: the skill states its budgets in wall-clock time (Quick: 2
  hours, critique 40 minutes) and treats a context time limit ("prepare
  in less than 2 hours") as a run limit. The agent part of a Normal run
  takes about 5 minutes (another session: "Brewed for 5m 18s", both
  lenses merged). So the time limit gave no reason to pick Quick: I
  recommended Quick only because of the context's 2-hour limit, and the
  user had to correct it. The real cost is the user's time in Converge
  (reading and answering items) and tokens.
- **Suggested change**: in `ml-critique` "Modes", say that the agent
  phases (Critique, Document, Check) take minutes in both modes. Express
  the Quick limits as user effort (items presented, converge rounds),
  not minutes. A context time limit is the user's prep time: it limits
  what to present and converge, not the agent's checks. Do not recommend
  Quick only because of a context time limit. Remove the minute values
  from the router table and the lenses ("40 minutes"), which also closes
  the declined "two sources for the Quick budget" entry.

## 2026-10-09 - ml-critique (tag the user's own findings)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: user-requested
- **Status**: adopted (2026-10-09): `ml-critique` step 3 and step 4,
  `ml-critique-merge`, `ml-critique-share-out` (ADR 0020).
- **Finding**: in Converge the user adds their own findings (new
  strengths, new questions for the author). The critique file mixes
  them with the lens findings, so a reader cannot tell who found what.
  The user asked: "separate my critique from your critique in all
  reports, if mine is new."
- **Suggested change**: in `ml-critique` step 3 and step 4: "Tag each
  new item that the user adds `[user]`, like `[ref]` for the reference
  pass. An item that only agrees with a lens item gets no tag. In the
  critique file, put `[user]` items in the same 4 parts, sorted with the
  sort key, and count them in the Summary."

## 2026-10-09 - ml-critique (Done well lists only real strengths)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: user-requested
- **Status**: adopted (2026-10-09), from the user's comment: `ml-critique`
  "Priority" and step 2, both lenses step 4. The cap is 5 (ADR 0020).
- **Finding**: the merged Done well part had 10 items. The user agreed
  with 2 and said the others "seem for encouragement". Items such as
  "train and test are both reported" or "stub rule with a count" are
  basic hygiene, not strengths that change a decision.
- **Suggested change**: in `ml-critique` step 2 part 1 and in both
  lenses: "List a strength only if losing it in a rewrite would make
  the result worse (a design choice to keep). Do not list basic hygiene.
  Maximum 5 in Normal mode. For each, say what breaks if it is lost."

## 2026-10-09 - ml-critique (share-out and merge skills)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: user-requested
- **Status**: adopted (2026-10-09): new skills `ml-critique-merge` and
  `ml-critique-share-out`; Quick mode removed (ADR 0020).
- **Finding**: the user, on the "critique time estimates" entry: "in all
  modes, research finished within minutes. 2 hours is overestimate." The
  real limit is the share-out (an interview, a team review), not the
  critique. No skill turns a full critique into what to discuss in a
  fixed time. The user also has 2 independent critiques of one report and
  no skill to merge them. The user named it "share-out", not
  "presentation", and asked for a separate merge skill.
- **Suggested change**: `ml-critique-merge`: critique files in; join,
  evidence, disagreements, tags, decisions; discuss until the user says
  to write; `critique/<date>-final.md` out. `ml-critique-share-out`: a
  final critique and a share-out context in (limit, format, topics,
  audience); discuss until "write"; `critique/<date>-share-out.md` out.

## 2026-10-09 - ml-critique* (skill-check fixes)
- **Project**: none (skill checks on the `ml-critique*` skills)
- **Source**: user-requested
- **Status**: adopted (2026-10-09): `ml-critique-share-out` step 2,
  Check, and Done when; `[C]` in `ml-critique` and both lenses; lens
  Check question 6; merge Check question 6; docs timeline (ADR 0021).
- **Finding**: the manual checklist found 5 problems: the docs timeline
  put credit after criticism; the share-out did not say whether a P1 or
  a required topic wins on a short limit; `[C]` had 2 meanings; the lens
  Checks did not test Done well; the merge Check did not test Context.
  The user decided: "credit before criticism", "don't cut p1", fix the
  rest.
- **Suggested change**: as applied (ADR 0021).

## 2026-10-09 - ml-design-principles.md, design and critique skills (intended behavior and change cadence)
- **Project**: none (lessons from a conference talk in the user's notes)
- **Source**: user-requested
- **Status**: adopted (2026-10-09): Principle 2; sys B7, F7; mod I12;
  sys H2, H3, I5 remedies; definition, high-level, deep-dive, delivery,
  and evaluate pointers (ADR 0022).
- **Finding**: the skills had no check that the model can game its
  metric, no check that one retrain fits inside the cadence of scheduled
  upstream changes, phase gates on the metric only, and no proven
  version kept shippable when a date depends on an unproven method. The
  user asked for general ML wording, with no domain words from the
  source and no names.
- **Suggested change**: as applied (ADR 0022).

## 2026-10-09 - ml-critique-merge, ml-critique (no top-3 cap: sort, do not cut)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: user correction
- **Status**: adopted (2026-10-09): "Top changes" in `ml-critique`;
  merge Propose, Write, Check; share-out Summary (ADR 0024).
- **Finding**: the merge proposal asked which item is "item 3" of the top
  3 (metric or label). The user: "this merge outcome doesn't limit to Top
  3 anyways. It is totally possible that after merging, there are top
  K>3 and they are all important. don't cut. Sort." A fixed top 3 hides
  P1 items of equal weight, and the cut belongs to the share-out.
- **Suggested change**: in `ml-critique-merge` (Propose, Write, Check)
  and `ml-critique` ("Top 3", step 2, step 4, Check): replace "top 3
  changes" with "top changes: every P1 item across the 4 parts, sorted
  with the sort key, each a single change". Only `ml-critique-share-out`
  selects a fixed number for time.

## 2026-10-09 - ml-critique, ml-critique-merge (context is mostly for the share-out)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: user correction
- **Status**: adopted (2026-10-09): "Critique context" in `ml-critique`;
  merge step 1 and Propose; lens step 7 and 6 (ADR 0024).
- **Finding**: on the merged Context section the user said: "you can keep
  the context. but note that context is mostly applied when create the
  share out, not critique or merge." The interview brief (time,
  sketches, audience, topic order) shapes what to say, not what is wrong
  with the design.
- **Suggested change**: in "Critique context" (`ml-critique`) and merge
  step 1: "The critique and the merge use the context only for the
  required parts and the scope. The time limit, the format, and the
  audience go to `ml-critique-share-out`. Record them in the Context
  section without a conflict entry."

## 2026-10-09 - ml-critique (requirements and cost analysis is P1)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: user correction
- **Status**: adopted with a change (2026-10-09). The user: "do a quick
  back of envelope analysis of reqs and cost analysis. Full one isn't
  possible without full design." Applied: system C2 `[C]` is a
  back-of-envelope estimate at the start; P1 example in `ml-critique`;
  Definition checklist and template (ADR 0024).
- **Finding**: the merge proposed P3 for "no stated latency, QPS, and
  cost", because the precompute makes latency trivial. The user: "No,
  beginning requirements analysis and cost is critical for industrial
  practice, may not be trivial after analysis, but always need analysis
  at the beginning." The reviewer cannot know the result is trivial
  until the analysis is done.
- **Suggested change**: in the `ml-critique` Priority table, P1 examples:
  add "no requirements and cost analysis at the start (scale, latency,
  cost)". In `ml-critique-system` catalog: mark the requirements item
  `[C]`. Do not lower it because the design looks cheap.

## 2026-10-09 - ml-system-design-prd, ml-critique, routers (Principle 2 skill-check fixes)
- **Project**: none (skill checks on the `ml-*` design and critique skills)
- **Source**: user-requested
- **Status**: adopted (2026-10-09): PRD step 3 and Check; `ml-critique`
  rule 4; "Related" in `ml-system-design` and `ml-modeling`; the
  `ml-system-design-definition` description (ADR 0023).
- **Finding**: the PRD had a copy of the Definition branches with no
  intended-behavior branch, so the PRD interview skipped it. The critique
  core and both routers named only Principle 1. Root cause: ADR 0022
  changed the Definition checklist, and the PRD copy did not follow.
- **Suggested change**: as applied (ADR 0023). Do not copy a checklist
  into another skill; point to it.

## 2026-10-09 - ml-design-principles.md, delivery, docs (Principle 3, Retraining item)
- **Project**: none (docs update after ADR 0022)
- **Source**: user-requested
- **Status**: adopted (2026-10-09): Principle 3 and the summary table;
  delivery Retraining item and Check question 6; Principle 3 pointers;
  `docs/ml-design-template.md` (ADR 0023, part 2).
- **Finding**: the user asked to bring the docs and the principles up to
  date with the production ideas of ADR 0022. 3 of its lessons had no
  principle, and delivery had no item for F7 (retrain cadence, owner),
  though the coverage map pointed F7 at delivery.
- **Suggested change**: as applied (ADR 0023). When a catalog item maps
  to a design skill in `coverage.md`, that skill needs a checklist item.

## 2026-10-09 - ml-critique lenses (an effect states a fact, not a failure)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found bug
- **Status**: proposed
- **Finding**: both lenses gave the C4 effect as a fact: "sigmoid(cos)
  stays in [0.27, 0.73]". The user had to ask why it matters. The real
  effect (easy pairs take as much gradient as hard pairs; pairs never
  saturate) took a second explanation. The skill already says "effect
  (the failure that can occur)", but the lens Check does not test it.
- **Suggested change**: add to each lens Check: "Does each effect name
  the failure in result terms (a wrong number, a worse top-K, a cost),
  not only a technical fact?"

## 2026-10-09 - ml-critique (question order: upstream data questions)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found bug
- **Status**: proposed
- **Finding**: the question "What did the stub filter remove?" came 16th
  of 17. The user moved it up: if the filter removed hubs, the most
  clicked targets and their clicks leave the data, so every later number
  changes. The sort key puts upstream first, but the lenses sorted
  questions by their own feel, not by the section of the item.
- **Suggested change**: in step 2 part 4, sort questions with the same
  sort key: a question about the data or the label (what was removed,
  filtered, or joined) comes before model and serving questions.

## 2026-10-09 - ml-critique-merge (a source that is itself a merge)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found better design
- **Status**: proposed
- **Finding**: one source (`final.md`) was a merge of v1 and v2, with
  IDs like `[v1:C1, v2:C2]`. The skill does not say whether the new
  file keeps those nested IDs or cites only the merged file. I cited
  `fin:F1` and added one Summary line that the fin items trace back to
  v1 and v2 in that file.
- **Suggested change**: in "Merge rules": "A source that is a merge: cite
  its own IDs (`fin:F1`), not its source IDs. Say in Summary and Sources
  where the older IDs are. Its decisions count as source decisions."
  Reason: nested IDs make each line long and are already in the file.

## 2026-10-09 - ml-critique-merge (label the disagreements)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found bug
- **Status**: proposed
- **Finding**: the Propose step numbers disagreements 1-16. The user
  answered with a bullet list that began "1: 'whole life line' use
  'life cycle'". It was a wording change, not an answer to disagreement
  1. I had to guess, and I said so in the reply.
- **Suggested change**: in Propose step 4: "Give each disagreement a
  label `X1, X2, ...`, distinct from item IDs. Ask the user to answer by
  label." Reason: plain numbers clash with the user's own list numbers.

## 2026-10-09 - ml-critique-merge (a source written under an older rule)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found better design
- **Status**: proposed
- **Finding**: v3 was written before ADR 0020 and 0024. It rated the
  missing requirements estimate P2 and listed the time limit as a
  context conflict. Today's rules say P1 and "not a conflict". The
  merge showed both as disagreements, which cost the user 2 answers
  with only one possible result.
- **Suggested change**: in "Merge rules": "If a source used a rule that
  has changed, apply the current rule. Record it under Sources,
  'Corrections that the merge kept', with the ADR. It is not a
  disagreement." Reason: the user should only decide real conflicts.

## 2026-10-09 - ml-critique-share-out (open choices at "write")
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: agent-found bug
- **Status**: proposed
- **Finding**: the proposal ended with 3 open choices (top-3 message 3,
  where to say the goal, the P2 block). The user said "write" with no
  answer. The merge skill sends open items to Deferred at "write"; the
  share-out skill has no rule. I used the proposal defaults and said so
  in the Summary.
- **Suggested change**: in Discuss: "At the 'write' request, each open
  choice takes the recommended option. Name each one in the Summary, so
  the user can change it." Reason: a share-out plan has no Deferred
  section, and the user must see what was chosen for them.

## 2026-10-09 - ml-critique-share-out (screen-shared file has tech content only)
- **Project**: `labs/ml-riot-wiki-recommender-1`
- **Source**: user-requested
- **Status**: proposed
- **Finding**: in the interview, the interviewer sees the screen. The
  share-out file mixed tech content with prep tips (timeline, minutes
  per block, "say", "follow-ups", "How to deliver", Cut list reasons
  "time"). The user asked to remove the tips and keep only the tech
  content. The fixed 8 sections then no longer apply.
- **Suggested change**: when the format includes screen share, write 2
  files: `share-out.md` (tech only: Summary with verdict and top 3, the
  4 required topics, sketches, other changes) and `share-out-prep.md`
  (Timeline, minutes, follow-up phrasing, Cut list, How to deliver).
  Run `check_doc.py --sections` on each with its own section list.
