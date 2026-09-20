---
name: ml-modeling-data
description: Use to profile a dataset before feature engineering — row counts, null rates, class balance, feature distributions, data-quality flags. Also creates the project's EDA notebook and bootstraps its Streamlit dashboard. Step 1 of the ml-modeling-* chain (data → features → train → evaluate). Trigger on "profile this data," "check data quality," "set up a dashboard for this," or continuing modeling work in an existing ml-<topic>-<n>/ project.
---

# Profile Data

Reads `<project-folder>/design/deep-dive.md`'s Data section (required — see
`ml-modeling` router if it's missing). Writes
`<project-folder>/modeling/01-data.md` and `modeling/01-data.json`, and
(Regular/Quick-POC only — see below) creates `dashboard/eda.ipynb` and
`dashboard/app.py`. First, run the "Deep-dive changed?" check from
`../ml-modeling/SKILL.md` (spec exists and its hash matches? proceed; otherwise
ask).

Mode: Regular asks about anything the data doesn't make obvious (e.g. why a null
rate is high). Quick POC states a reasonable read and moves on — see
`ml-modeling` router for the keyword rule.

## Profile

- **Shape**: row count, column count, memory footprint.
- **Nulls**: per-column null rate; flag any column above ~20% as a modeling
  risk, not just a number to report.
- **Target/label**: class balance (classification) or distribution shape
  (regression) — this is what decides whether class-imbalance handling matters
  later.
- **Feature distributions**: numeric columns — min/max/mean/std, skew;
  categorical columns — cardinality, top values.
- **Quality flags**: duplicated rows, obvious outliers, columns that don't match
  `design/deep-dive.md`'s stated Data section (a real source drifted from the
  design, or the design was wrong — either way, surface it, don't silently
  reconcile).

Write the same facts to `modeling/01-data.json` (the dashboard reads this, not
the `.md`):

```json
{
  "shape": {"rows": 0, "columns": 0, "memory_mb": 0.0},
  "nulls": {"<col>": 0.0},
  "target": {"column": "<name>", "type": "classification|regression", "class_balance": {}, "distribution": {}},
  "numeric_distributions": {"<col>": {"min": 0, "max": 0, "mean": 0, "std": 0, "skew": 0}},
  "categorical_distributions": {"<col>": {"cardinality": 0, "top_values": {}}},
  "quality_flags": ["<string>"]
}
```

## Dashboard (Regular/Quick-POC only)

Never in monkey-mode, which stays fully separate per
`ml-system-design-monkey-mode`. Deliberately narrow — the dashboard's job is
"understand the project and progress at a glance," not mirror every file. Only
two sections exist: this one (EDA) and Results (from `ml-modeling-evaluate`),
plus an optional model-comparison section if `ml-modeling-multiagent` ran. Full
rationale in `../adr/0002-modeling-dashboard.md`. Feature engineering and
training detail deliberately stay out — `ml-modeling-features`/`-train`/
`-multiagent` are untouched by this and don't write anything for the dashboard.

**EDA notebook**: build `dashboard/eda.ipynb` with real code cells (shape,
nulls, target balance, distributions — the same facts as above, as executable
cells) using `nbformat`, then run `uv run jupyter nbconvert --to notebook
--execute --inplace dashboard/eda.ipynb` so it has real executed outputs, not
empty template cells.

**Dashboard app** — copy `assets/dashboard_app.py` to
`<project-folder>/dashboard/app.py` once (no later step ever edits this file,
only the JSON it reads). It's a generic reader — nothing in it needs per-project
editing, since it reads standardized paths (`../modeling/01-data.json`,
`../modeling/04-evaluate.json`, `../modeling/train-candidates/*/metrics.json`)
and renders one tab per file it finds. Design intent: compact and minimal — tabs
instead of stacked sections, tightened CSS (small headers, small metric fonts,
low padding), short chart heights (~220px). If the design ever needs another
pass, edit `assets/dashboard_app.py` here (the single source of truth) and
re-copy it into any project that should pick up the change — don't hand-edit a
project's own `dashboard/app.py` and let it drift from the template.

Launch it on a per-project port, so two projects' dashboards never collide: pick
the first port from 8501 upward where `lsof -nP -iTCP:<port> -sTCP:LISTEN`
prints nothing, write it to `dashboard/.port`, then `uv run streamlit run
dashboard/app.py --server.headless true --server.port $(cat dashboard/.port) &`
(background — don't block the conversation), and report
`http://localhost:<port>` to the user. `dashboard/.port` is the one place the
port lives; `ml-modeling-evaluate` reads it for its health check.

Done when every profile flag above is a real number from the actual data (not
"looks fine"), `modeling/01-data.md` states which columns are risky and why,
`01-data.json` matches it, `dashboard/eda.ipynb` has real executed outputs, and
the Streamlit process is actually running and reachable at the reported URL —
not just files written.

If this run turns up a bug or a better design in this skill, or you ask for a
change to how it works, log it — see `../ml-modeling/SKILL.md`'s Skill
improvement log.
