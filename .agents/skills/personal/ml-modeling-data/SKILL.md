---
name: ml-modeling-data
description: Use to profile a dataset before feature engineering — row counts, null rates, class balance, feature distributions, data-quality flags. Also creates the project's EDA notebook and bootstraps its Streamlit dashboard. Step 1 of the ml-modeling-* chain (data → features → train → evaluate). Trigger on "profile this data," "check data quality," "set up a dashboard for this," or continuing modeling work in an existing ml-<topic>-<n>/ project.
---

# Profile Data

Reads `<project-folder>/design/deep-dive.md`'s Data section (required — see `ml-modeling` router if it's missing). Writes `<project-folder>/modeling/01-data.md` and `modeling/01-data.json`, and (Regular/Quick-POC only — see below) creates `dashboard/eda.ipynb` and `dashboard/app.py`.

Mode: Regular asks about anything the data doesn't make obvious (e.g. why a null rate is high). Quick POC states a reasonable read and moves on — see `ml-modeling` router for the keyword rule.

## Profile

- **Shape**: row count, column count, memory footprint.
- **Nulls**: per-column null rate; flag any column above ~20% as a modeling risk, not just a number to report.
- **Target/label**: class balance (classification) or distribution shape (regression) — this is what decides whether class-imbalance handling matters later.
- **Feature distributions**: numeric columns — min/max/mean/std, skew; categorical columns — cardinality, top values.
- **Quality flags**: duplicated rows, obvious outliers, columns that don't match `design/deep-dive.md`'s stated Data section (a real source drifted from the design, or the design was wrong — either way, surface it, don't silently reconcile).

Write the same facts to `modeling/01-data.json` (the dashboard reads this, not the `.md`):

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

## Dashboard (Regular/Quick-POC only — never in monkey-mode, which stays fully separate per `ml-system-design-monkey-mode`)

Deliberately narrow — the dashboard's job is "understand the project and progress at a glance," not mirror every file. Only two sections exist: this one (EDA) and Results (from `ml-modeling-evaluate`), plus an optional model-comparison section if `ml-modeling-multiagent` ran. Full rationale in `../adr/0002-modeling-dashboard.md`. Feature engineering and training detail deliberately stay out — `ml-modeling-features`/`-train`/`-multiagent` are untouched by this and don't write anything for the dashboard.

**EDA notebook**: build `dashboard/eda.ipynb` with real code cells (shape, nulls, target balance, distributions — the same facts as above, as executable cells) using `nbformat`, then run `uv run jupyter nbconvert --to notebook --execute --inplace dashboard/eda.ipynb` so it has real executed outputs, not empty template cells.

**Dashboard app** — create `dashboard/app.py` once (no later step ever edits this file, only the JSON it reads):

```python
import json
from pathlib import Path
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
MODELING_DIR = PROJECT_DIR / "modeling"

st.set_page_config(page_title="ML Project Dashboard", layout="wide")
st.title("ML Project Dashboard")

data_json = MODELING_DIR / "01-data.json"
if data_json.exists():
    d = json.loads(data_json.read_text())
    st.header("Data (EDA)")
    # render shape/nulls/target balance/distributions from d, with plotly charts
else:
    st.info("Run ml-modeling-data to populate this section.")

candidates_dir = MODELING_DIR / "train-candidates"
if candidates_dir.exists():
    st.header("Model Comparison")
    # read each */metrics.json, bar chart by primary metric

eval_json = MODELING_DIR / "04-evaluate.json"
if eval_json.exists():
    e = json.loads(eval_json.read_text())
    st.header("Final Results")
    # render metrics vs. baseline, verdict
else:
    st.info("Run ml-modeling-evaluate to populate this section.")
```

Launch it: `uv run streamlit run dashboard/app.py --server.headless true &` (background — don't block the conversation), then report the local URL (`http://localhost:8501`) to the user.

Done when every profile flag above is a real number from the actual data (not "looks fine"), `modeling/01-data.md` states which columns are risky and why, `01-data.json` matches it, `dashboard/eda.ipynb` has real executed outputs, and the Streamlit process is actually running and reachable at the reported URL — not just files written.
