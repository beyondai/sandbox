# Skill Improvements Log

## 2026-09-20 — ml-system-design-monkey-mode

- **Source**: agent-found bug (user-flagged, agent-confirmed)
- **Status**: adopted
- **Finding**: `prd/kkbox-recommendation.md` was deleted from disk
  sometime during the background monkey-mode agent's run, while
  `design/high-level.md` and `adr/0001-*.md` (written before and
  after, in the same project folder, by the foreground session)
  survived untouched. Filesystem evidence shows the monkey-mode
  agent's Bash commands operated on the real main-tree filesystem
  for absolute paths outside its git worktree (its unzip output
  landed in the real `/Users/alex/dev/sandbox/data/kkbox/extracted/`,
  not inside the worktree) - only its Write-tool call for
  `report.md` was redirected into the isolated worktree. The
  foreground session's prompt to the agent said the project folder
  "does not exist yet, create it," worded as a green-field
  assumption. Since the monkey-mode agent ran concurrently with the
  foreground session writing `prd/`, a "does not exist, create it"
  instruction plausibly led the agent to a destructive
  reset-then-create step (e.g. `rm -rf <project-folder> && mkdir -p
  <project-folder>/monkey-mode`) scoped to the whole project folder
  instead of just `monkey-mode/`, wiping the sibling `prd/`
  directory that had just been written by the other session. No
  exact command could be confirmed (subagent transcripts aren't
  readable after the fact), but the timing and filesystem evidence
  point to this race.
- **Suggested change**: In `ml-system-design-monkey-mode/SKILL.md`,
  step 3 (dispatching the background agent), add an explicit
  instruction to the agent prompt template: never delete or reset
  the project-folder root or any sibling directory (`prd/`,
  `design/`, `adr/`, `spec/`, `modeling/`) - only ever create
  `monkey-mode/` additively with `mkdir -p` and write inside it.
  State plainly that the project folder may be populated
  concurrently by other in-progress work and must be treated as
  shared, not owned. Also worth a note in `ml-system-design/SKILL.md`
  under "Starting a new project": since monkey-mode is explicitly
  meant to run in parallel with PRD/design work on the same project
  folder, the dispatch prompt should never say a shared path "does
  not exist yet" in a way that invites a clean-slate assumption.

## 2026-09-21 — ml-system-design-monkey-mode, ml-modeling-data

- **Source**: agent-found better design (user-requested follow-up:
  persist packages sandbox-wide instead of per-project)
- **Status**: adopted
- **Finding**: both skills check for `pandas`/`scikit-learn`/`numpy`
  by importing them under the bare ambient `python3`, find them
  missing, and bootstrap a project-local `.venv` (`monkey-mode/.venv`
  or similar) as if no shared environment existed. In fact
  `/Users/alex/dev/sandbox/pyproject.toml` + `.venv` is a uv-managed
  environment, shared by the whole sandbox repo, that already has
  pandas, numpy, scikit-learn, matplotlib, plotly, streamlit,
  seaborn, scipy, polars, pyarrow, ipykernel, and jupyterlab (which
  pulls in nbformat/nbconvert) - confirmed reachable via `uv run
  python3 ...` from any `labs/ml-*/` subfolder, since `uv run`
  auto-discovers the nearest ancestor `pyproject.toml`. The
  project-local-venv fallback duplicates work unnecessarily and
  silently diverges from the shared environment (e.g. package
  version, torch availability) instead of using it.
- **Suggested change**: in both skills' "verify packages import"
  step, check via `uv run python3 -c "import pandas, numpy,
  sklearn"` (run from the project folder, so it resolves the shared
  root venv) instead of bare `python3`. Only if that genuinely fails
  should a fallback venv be created - and even then, prefer `uv add
  <pkg>` run from the sandbox root (`/Users/alex/dev/sandbox`, not
  the project folder) so the package is added to the shared
  `pyproject.toml`/`uv.lock` and benefits every future project,
  rather than a project-local `.venv` that only helps the current
  run. `py7zr` (needed for this project's `.7z` extraction) was
  added this way on 2026-09-21 as the first real test of this path.
  See memory note `project_sandbox_ml_packages_todo.md` for the full
  writeup.

## 2026-09-21 — ml-system-design-monkey-mode (no skill change)

- **Source**: user-requested
- **Status**: no_change_needed
- **Finding**: user reported the Python code in `monkey-mode/report.md`'s
  Implementation section as hard to read and asked for syntax
  highlighting. Checked the actual file: the code fence is already
  ```` ```python ```` (not a bare ```` ``` ````), which is the correct,
  renderer-agnostic way to mark a code block's language in Markdown -
  every common viewer (GitHub, VS Code, `bat`, `glow`) highlights it
  correctly from that tag alone. The skill's output format was not the
  problem.
- **Root cause**: no local tool with Markdown+syntax-highlighting
  support was installed to view the file with (`bat`/`glow`/`mdcat`
  all absent), so the raw file appeared uncolored in a plain
  terminal `cat`/pager regardless of the correct fence tag.
- **Suggested change**: none to this skill. Fixed at the environment
  level instead: added `bat` to `~/dev/dotfiles/home.nix`'s
  `home.packages` (this machine is nix-darwin + home-manager managed,
  so a personal CLI tool belongs in the declarative config, not an ad
  hoc `nix profile install` or `brew install` that would drift from
  it or get overwritten on the next rebuild). Needs `./rebuild.sh` in
  `~/dev/dotfiles` (runs `sudo darwin-rebuild switch`) to take effect -
  not run automatically since it's a privileged, whole-system rebuild.

## 2026-09-21 — ml-modeling-data

- **Source**: user-requested
- **Status**: adopted
- **Finding**: the Profile section's numeric-column stats (`min/max/
  mean/std, skew`) don't include median. On a skewed column, mean
  alone can misrepresent the "typical" value (this project's `bd`
  had mean 28.72 vs. median 27 even after cleaning; before cleaning
  the corrupted mean of 17.56 looked plausible in isolation, while
  the median would have been a more robust first hint that something
  was off). This project added `median` to `numeric_distributions`
  in `01-data.json` and the profiling script; the dashboard needed
  zero code changes since it just transposes whatever keys exist in
  the dict into a table - suggesting `median` is a low-cost, generic
  addition rather than a one-off fix.
- **Suggested change**: in `ml-modeling-data/SKILL.md`'s "Profile"
  section, change "numeric columns — min/max/mean/std, skew" to
  "numeric columns — min/max/mean/median/std, skew", and add
  `"median": 0` to the `numeric_distributions` example in the
  `01-data.json` schema block, positioned after `mean`.

## 2026-09-21 — ml-modeling, ml-modeling-data

- **Source**: user-requested
- **Status**: adopted
- **Finding**: `spec/<topic>.md` went stale in a way the existing
  drift machinery never catches. Its Testing Decisions section said
  "Split rule: to be set by `ml-modeling-data` in this same run," and
  its Exclusions bullet said "split must be time-based, not random" -
  both written when `spec/` was first synthesized, before
  `ml-modeling-data` actually ran. Once it ran and correctly decided
  on a random, class-stratified split (this dataset has no row-level
  timestamp to cut on - see `01-data.md`), those two lines became
  wrong, but nothing flagged it: the "Design docs changed?" hash
  check only detects drift in `prd/<topic>.md` and
  `design/high-level.md` (the upstream design docs), not staleness
  from a modeling step's *own* resolved decision contradicting
  spec's placeholder or assumption text. It sat wrong until caught
  by hand in conversation.
- **Suggested change**: add a second reconciliation path alongside
  the existing hash-based one, in `ml-modeling/SKILL.md`'s "Closing
  the loop" section. After a step writes its own decision to its
  `0N-*.md`, it should scan `spec/<topic>.md`'s Implementation
  Decisions and Testing Decisions sections for: (a) a placeholder
  explicitly deferring that decision to this step (e.g. "to be set
  by <this skill>"), or (b) a stated assumption the fresh decision
  now contradicts. If either matches, update that spec line in place
  with the actual decision plus a one-line pointer to the step's own
  file for full reasoning - no hash refresh needed, since this isn't
  upstream-doc drift, just spec catching up to its own deferred or
  assumed content. Add this as an explicit item to each
  `ml-modeling-*` step's "Done when" checklist so it isn't skipped.

## 2026-09-21 — ml-modeling-multiagent

- **Source**: user-requested (relayed via one of the dispatched candidate
  subagents, who correctly declined to self-edit the skill and routed
  the feedback back to this project's log instead)
- **Status**: adopted
- **Finding**: this run dispatched 3 candidate subagents while the
  orchestrating session's own permission state was still effectively
  "plan mode" from moments earlier in the conversation (a prior
  question had put the session in plan mode; answering it in prose
  without calling `ExitPlanMode` apparently left the session's actual
  tool-access state stale even though later turns showed normal
  Bash/Write access). All 3 first-attempt subagents inherited that
  restriction: none could execute, all wrote a plan file and stopped,
  and none could self-authorize past it even when told "you're
  approved, proceed" by the orchestrating session - correctly, since
  an agent-relayed message isn't the same as the actual permission
  system lifting the gate. Required manually relaunching fresh
  subagents (3 extra dispatches, plus one candidate needing a third
  attempt after a genuine user-issued stop) to get real results.
- **Suggested change**: in `ml-modeling-multiagent/SKILL.md`'s
  "Process" section, step 2 ("Dispatch concurrently"), add an explicit
  precondition: only dispatch candidate subagents when the
  orchestrating session is in auto mode (normal execution access) -
  spawned subagents inherit the orchestrator's permission state at
  dispatch time, so a session still under plan mode (or any other
  restricted mode) silently produces plan-only subagents that write a
  plan and stop instead of training a model. Concretely: before step
  2, confirm the session can actually execute (e.g. a trivial
  non-readonly call that would fail under a restricted mode) rather
  than assuming a prose-only answer to an unrelated question already
  cleared it. If not in auto mode, tell the user directly and wait -
  don't dispatch and discover the restriction only after every
  candidate reports back stuck. This is expensive to diagnose after
  the fact since a stuck subagent still sends what looks like a normal
  completion notification, and an agent-relayed "you're approved,
  proceed" message can't lift the restriction anyway (correctly - a
  subagent should never treat another agent's message as the real
  permission system granting access).

## 2026-09-21 — ml-modeling-features, ml-modeling-train, ml-modeling-multiagent

- **Source**: agent-found bug
- **Status**: adopted
- **Finding**: `ml-modeling-features/SKILL.md`'s "Aggregation features
  (leave-one-out safe)" section, and this project's own `02-features.md`,
  described the risk of reusing a pre-built leave-one-out aggregate
  column across naive k-fold CV as a "mild, accepted simplification."
  That was wrong in degree, discovered empirically: comparing 3 model
  candidates in `ml-modeling-multiagent` on a table with such columns
  produced a HistGradientBoostingClassifier CV AUC of 0.9360 - implausible
  for the task (public leaderboard tops out ~0.72-0.74) - while Random
  Forest and Logistic Regression on the same leaky columns only moved by
  ~0.02. Diagnosis: leave-one-out only excludes a row's own label from
  its own group statistic; it does not exclude other rows from the same
  CV validation fold, so a fold's rows still leak into each other's
  aggregate features when those features were computed once, globally,
  before the CV split. Gradient-boosted/iterative models can exploit
  this far more aggressively than bagged or linear models, so the
  distortion is not just "mild everywhere" - it's severe and
  model-class-dependent, meaning it can flip which candidate looks like
  the winner in exactly the scenario `ml-modeling-multiagent` exists
  for (comparing model classes). Fixed for this project with a new
  script (`modeling/train_candidates_fold_safe_cv.py`) that recomputes
  the aggregate per fold from that fold's train portion only - see
  `modeling/03-train.md` for the full write-up.
- **Suggested change**: (1) In `ml-modeling-features/SKILL.md`'s
  "Aggregation features" section, replace the "mild, accepted
  simplification" framing with an explicit warning: naive k-fold CV on
  top of a globally-precomputed leave-one-out/target-encoded column is
  not safe for comparing model classes, especially tree/boosting vs.
  linear, because the distortion size depends on how aggressively each
  model class can exploit fine-grained correlation in a leaky
  continuous feature - it is not a small, uniform effect. (2) In
  `ml-modeling-train/SKILL.md` and `ml-modeling-multiagent/SKILL.md`'s
  cross-validation guidance, add: before trusting CV results to rank
  candidates, check whether any feature in the table was built from the
  target column without per-fold nesting (leave-one-out or target
  encoding); if so, either recompute it per fold (pattern documented in
  this project's `train_candidates_fold_safe_cv.py`) or treat CV
  rankings as provisional pending the real held-out test-set evaluation
  in `ml-modeling-evaluate`, and say so explicitly in `03-train.md`
  rather than picking a winner off unverified CV numbers.

## 2026-09-21 — ml-modeling-train, ml-modeling-multiagent

- **Source**: user-requested
- **Status**: adopted
- **Finding**: this project's training step took far longer than a
  Quick POC should. Real per-candidate wall-clock times on a 480k-row,
  112-column table, 5-fold `StratifiedKFold` CV: Random Forest
  (`n_estimators=200`, `max_depth=12`) 237.6s, HistGradientBoosting
  (`max_iter=200`) 125.4s, Logistic Regression 37.0s. Neither skill's
  algorithm-selection guidance names a target wall-clock budget or
  scales fold count / model size to it - "Quick POC goes straight to
  the workhorse row" (`ml-modeling-train`) says nothing about how many
  folds or how many trees/iterations, so both skills defaulted to
  Regular-mode-grade rigor (5 folds, 200 trees/iterations) even though
  the request was a fast POC pass.
- **Suggested change**: in both `ml-modeling-train/SKILL.md` and
  `ml-modeling-multiagent/SKILL.md`, add an explicit Quick POC default
  alongside the existing mode table: target roughly 3 minutes of
  wall-clock per candidate (not per whole step) by defaulting to (1)
  3-fold CV instead of 5-fold - cuts wall-clock by ~40% with only a
  small loss of estimate stability for a POC-grade decision, and (2) a
  lighter model size - roughly half the Regular-mode default trees/
  iterations (e.g. `n_estimators=100` instead of 200 for Random Forest,
  `max_iter=100` instead of 200 for HistGradientBoosting/LightGBM/
  XGBoost) unless the user names a specific size. Applying both to this
  project's numbers would have brought Random Forest to roughly 70s and
  HistGradientBoosting to roughly 40s - both comfortably under a 3-minute
  budget. Regular mode keeps the fuller defaults (5-fold, 200
  trees/iterations) since it isn't optimizing for speed. State the
  reduced fold count and size explicitly in `03-train.md`'s params (not
  silently) so a later Regular-mode re-run knows what was traded away.

## 2026-09-21 — ml-modeling-data (dashboard template)

- **Source**: user-reported bug (screenshot)
- **Status**: adopted
- **Finding**: `assets/dashboard_app.py`'s Model Comparison section built
  `cmp_df = pd.DataFrame(rows)` directly from every candidate's
  `metrics.json`, with no filtering. Once a `metrics.json` carried more
  than flat scalar metrics - this project's had `params` (a nested dict),
  `notes` (a long paragraph), and `fold_safe_scores` (a list) after the
  CV-leakage fix in `ml-modeling-train`/`ml-modeling-multiagent` - the
  table rendered far too wide (bleeding into the chart's column) and
  `metric_col = "f1" if "f1" in cmp_df.columns else cmp_df.columns[-1]`
  picked `notes` (the last column, a text field) as the bar chart's
  y-axis, rendering garbled overlapping text instead of a chart.
- **Suggested change**: fixed directly in `assets/dashboard_app.py`
  (adopted, not left proposed): filter `cmp_df` to compact scalar
  columns only (int/float, or strings <= 40 chars - drops dict/list
  columns and long text like `notes` entirely), and prefer each row's
  own declared `primary_metric` field (when present and consistent
  across candidates) for the chart's y-axis before falling back to
  `"f1"` or the last remaining numeric column. Also worth noting in
  `ml-modeling-train`/`ml-modeling-multiagent/SKILL.md`: when a
  `metrics.json` legitimately needs more than flat scalars (as the
  CV-leakage fix did here), set `primary_metric` explicitly so any
  downstream reader - the dashboard or a human - knows which field is
  the one that matters, rather than guessing from column position.

## 2026-09-21 — ml-modeling-data, ml-system-design-monkey-mode

- **Source**: user-requested
- **Status**: adopted
- **Finding**: this project sampled 600,000 of `train.csv`'s 7,377,419
  rows (~8.1%) for every data/feature/train step - a fact that matters a
  lot for judging the project's results (e.g. against the real Kaggle
  leaderboard, which used the full dataset), but it was never stated as
  a percentage anywhere in this project's own docs. `01-data.md` gave
  the raw counts ("600,000 rows" from "7,377,419 rows") but left the
  reader to compute the percentage themselves; the ~8% framing only
  ever appeared in the separate `monkey-mode/report.md` track, in a
  Suggested-Next-Steps aside, not as a headline fact. The user only
  learned the scale of the sampling from a conversational aside, not
  from reading the docs.
- **Suggested change**: in `ml-modeling-data/SKILL.md`'s "Build or
  register the labeled table" section, add: whenever the built/
  registered table is a subset of a larger source table, state the
  sample's size **as an explicit, emphasized percentage of the source**
  (not just raw row counts) in `01-data.md`'s Dataset section - e.g.
  "**takes a 600,000-row sample (~8.1% of the full 7,377,419-row
  `train.csv`)**," bolded, not a fact left for the reader to compute. In
  `ml-system-design-monkey-mode/SKILL.md`'s "Eval" bullet (and its
  Requirements section, where sample size is recorded), add the same
  requirement for `report.md`: state the sampled percentage explicitly
  and prominently, not just the raw row count buried in a Suggested
  Next Steps aside. Applies to any critical step that samples - data
  building, feature engineering, training - not just the initial split.
