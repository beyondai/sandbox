---
name: ml-modeling-data
description: >-
  Use to profile a dataset before feature engineering - row counts, null rates,
  class balance, feature distributions, data-quality flags - and clean genuine
  errors it finds (impossible values, sentinel-coded missingness, exact
  duplicates). Also creates the project's EDA notebook and bootstraps its
  Streamlit dashboard. Step 1 of the ml-modeling-* chain (data → features →
  train → evaluate → serve). Trigger on "profile this data," "check data quality,"
  "clean this data," "set up a dashboard for this," or continuing modeling
  work in an existing ML project folder. Builds the labeled table first
  when the source is raw logs rather than a flat labeled table, and records
  the table paths, label, and split in `01-data.json`'s `dataset` block - the
  contract every later step reads.
---

# Profile Data

Contents: 1. Design docs changed? | 2. Build or register the labeled table | 3.
Profile | 4. Clean | 5. Dashboard | 6. Check

- **Reads:** `<project-folder>/design/high-level.md` (ML framing,
  Architecture source tables) and `prd/<topic>.md` (scope). Both are
  required (see `../ml-modeling/SKILL.md`, "Required upstream").
- **Writes:** `modeling/01-data.md`, `modeling/01-data.json`. Regular and
  Quick POC also write `dashboard/eda.ipynb` and `dashboard/app.py`.
- **Rules:** `../ml-system-design/SKILL.md`, "Project folder", "Output
  docs", "Check the output", "Skill improvement log".
- **Mode:** Regular asks about each fact that the data does not make
  clear (for example, a high null rate). Quick POC states a reasonable
  reading and continues.

Progress (copy into your reply, tick each line):

```
[ ] 1 Design docs changed? (spec_hash_check.sh)
[ ] 2 Build or register the labeled table; set the split
[ ] 3 Profile the train table
[ ] 4 Clean; profile again
[ ] 5 Dashboard (not in monkey-mode)
[ ] 6 Check
```

## 1. Design docs changed?

Run the check in `../ml-modeling/SKILL.md`, "Design docs changed?".

## 2. Build or register the labeled table

Read the ML framing (target, label definition and horizon, scoring
population, unit, exclusions) and the Architecture source tables. One
model and one `dataset` block for each project folder. If the framing
names several models, build the one that "This folder builds" names.

- **A flat labeled table exists** (a CSV with the label column): register
  it. Fill the `dataset` block with its paths, label, id, and split. If no
  test split exists, make one here: random with a fixed seed, unless the
  labels have time windows.
- **The source is raw logs** (events, activity, transactions; no label
  column): write `modeling/build_dataset.py`, and run it with `uv run
  python3`. It applies the label definition, horizon, population, and
  exclusions from the framing. It writes
  `modeling/datasets/<task>_train.csv` and `<task>_test.csv`.
  - **Large tables** (over about 1M rows): write parquet under the
    sandbox-root `data/<dataset>/modeling/`, not CSV in the project
    folder. CSV at that size is slow and large, and generated data stays
    out of git. Check each path with `git check-ignore -v`. Record the
    paths in the `dataset` block (relative to `modeling/`).
  - **Ranking tasks:** one row is a (query, candidate) pair. Record the
    query column as `dataset.group`, and write a truth table for each
    split with every true item per query, also items that no candidate
    rule found. Recall metrics need it (`truth_train`, `truth_test`).
  - Features use only rows before the cutoff. Labels use only rows at or
    after the cutoff.
  - Assert that the positive rate is not near 0% or 100%. A degenerate
    rate shows a leak or a wrong rule. (This assert found a real 100%
    churn look-ahead bug.)
  - **Implicit labels** (the logs hold only positives, such as clicks or
    listens): build the negatives here, from the plan in high-level or
    the "Negative sampling" section of `../ml-model-training.md`.
    Exclude the user's own positives and items not available at that
    time. Build test negatives from the production distribution (real
    impressions or all candidates), not from the training negatives.
    Record the types, ratio, and pool in `dataset.negatives`.
  - Keep the script small and able to run again. It is part of the
    record.

Run code with `uv run --project <sandbox root>`, so a project outside the
repo also uses the shared venv (pandas, numpy, scikit-learn, the dashboard
packages). For a new package, run `uv add <pkg>` at the sandbox root.

**The split is this step's decision.** For labels with time windows, use
2 cutoffs:
- The test cutoff is late enough that its label window closes inside the
  data.
- The train cutoff is at least one horizon earlier. No train label
  overlaps the test window.
- Do not put a cutoff inside a seasonal event that the framing names.

Record the cutoffs in the `dataset` block. Add a "Dataset" section to
`01-data.md`: the same facts as the block, in prose, with the reasons for
the cutoffs.

**A sample of a larger table:** state its size in "Dataset" as a bold
percentage of the source. Example: "**takes a 600,000-row sample (~8.1% of
the full 7,377,419-row `train.csv`)**". Results are compared with
benchmarks on the full data later.

## 3. Profile

Profile the train table only. Never read test rows here.

- **Shape:** rows, columns, memory.
- **Nulls:** the null rate for each column. A column over ~20% is a
  modeling risk: say why.
- **Target:** the class balance (classification) or the distribution
  (regression). This decides if imbalance handling is necessary.
- **Distributions:** numeric: min, max, mean, median, std, skew.
  Categorical: cardinality, top values.
- **Quality flags:** duplicate rows, outliers, and sources or columns that
  are different from the Architecture in `design/high-level.md`. Tell the
  user about a difference, and offer to update high-level (see "Closing the
  loop" in `../ml-modeling/SKILL.md`).

Write the same facts to `modeling/01-data.json`. The dashboard reads the
JSON, not the `.md`.

```json
{
  "dataset": {
    "train": "datasets/<task>_train.csv",
    "test": "datasets/<task>_test.csv",
    "label": "<col>", "id": "<col>",
    "group": "<query col, ranking only>",
    "truth_train": "<path, ranking only>", "truth_test": "<path, ranking only>",
    "split": {"type": "cutoff|random", "train_cutoff": 0, "test_cutoff": 0,
              "horizon_days": 0, "seed": 0, "test_share": 0.0},
    "exclusions": ["<rule>"],
    "negatives": {"types": ["random", "hard"], "ratio": 0, "pool": "<rule>",
                  "correction": "<none|logQ|downsample rate>"},
    "built_by": "modeling/build_dataset.py|registered"
  },
  "shape": {"rows": 0, "columns": 0, "memory_mb": 0.0},
  "nulls": {"<col>": 0.0},
  "target": {"column": "<name>", "type": "classification|regression",
             "class_balance": {}, "distribution": {}},
  "numeric_distributions": {"<col>": {"min": 0, "max": 0, "mean": 0,
                                      "median": 0, "std": 0, "skew": 0}},
  "categorical_distributions": {"<col>": {"cardinality": 0, "top_values": {}}},
  "quality_flags": ["<string>"]
}
```

## 4. Clean

For each quality flag, ask: would a domain expert call this impossible,
or only unusual? Reason: `../adr/0007-clean-phase-in-data-step.md`.

- **Impossible: fix it here.** Examples: a negative or 200-year age, a
  sentinel for missing (`0` for "unknown" where `0` is also valid), an
  exact duplicate row, a null made by the reader (pandas reads the string
  "NA", for example North America, as null; use `keep_default_na=False`
  for that column).
  - Set the invalid value to null. Do not drop the row: it has other
    valid features. Drop only exact duplicates.
  - Fix it in the build step (`build_dataset.py`, or the registration).
  - Profile again, so `01-data.md` and `01-data.json` show the cleaned
    numbers. A stale profile next to a cleaned table misleads every later
    step. Mark each flag in `quality_flags` as cleaned or kept.
- **Unusual: keep it, and keep the flag.** Examples: a long but real song,
  a large but real purchase, an old account. It is signal, not error.

For a fix that changes the data, record in `01-data.md` what changed, why,
and a before/after statistic. Example: "skew dropped from 22.26 to 1.3",
not only "191858 rows masked".

Quick POC classifies the flags without questions. Regular asks when a
flag is ambiguous.

## 5. Dashboard

Regular and Quick POC only. Never in monkey-mode. Scope: EDA here, and
Results from `ml-modeling-evaluate`. Reason:
`../adr/0002-modeling-dashboard.md`.

Requires streamlit, plotly, pandas, and jupyterlab in the sandbox venv. If
one is missing: `uv add streamlit plotly pandas jupyterlab` at the sandbox
root.

1. **EDA notebook.** Build `dashboard/eda.ipynb` with `nbformat`. Its code
   cells compute the facts of step 3. Execute it:

   ```
   uv run --project <sandbox root> jupyter nbconvert --to notebook --execute --inplace dashboard/eda.ipynb
   ```

2. **App.** Copy `assets/dashboard_app.py` to `dashboard/app.py` once.
   No later step edits it. It reads `../modeling/01-data.json`,
   `../modeling/04-evaluate.json`, and
   `../modeling/train-candidates/*/metrics.json`. To change the design,
   edit `assets/dashboard_app.py` (the single source of truth) and copy
   it again.
3. **Launch.** Run:

   ```
   bash .agents/skills/personal/ml-modeling-data/scripts/launch_dashboard.sh <project-folder>
   ```

   It selects a free port from 8501, writes `dashboard/.port` and
   `dashboard/.pid`, starts streamlit in the background, and prints the
   URL. Give the URL to the user. `ml-modeling-evaluate` reads
   `dashboard/.port`. An optional session-exit hook (in the user's
   dotfiles) uses `dashboard/.pid`.

## 6. Check

Do "Check the output" in `../ml-system-design/SKILL.md`. Intent questions:
1. Does the label follow the framing's definition, horizon, population,
   and exclusions? Is the positive rate plausible? For implicit labels,
   are the negatives recorded, and are test negatives from production?
2. Can no train label overlap the test window? Is each feature from before
   its cutoff?
3. Is each profile value a real number from the data, not "looks fine"?
4. Is each quality flag either cleaned and profiled again, or recorded as
   a risk? Does `01-data.json` match `01-data.md`?

Done when:
- The 4 answers are yes, and `check_doc.py` prints `OK`.
- The `dataset` paths resolve.
- `01-data.md` states the risky columns and why.
- `dashboard/eda.ipynb` has executed outputs, and the URL responds.
- A spec line that deferred or assumed the split is updated (see "Closing
  the loop" in `../ml-modeling/SKILL.md`).
