# Modeling Step 1 — Data (Quick POC)

No mode keyword in this request. Continuing Quick POC to match this
project's established pace (`prd/` and `design/high-level.md` were both
explicitly Quick POC) — states a reasonable read and moves on rather than
asking round by round.

Design docs changed? First run for this project: no `spec/kaggle-churn.md`
existed yet, so one was synthesized from `prd/kaggle-churn.md` +
`adr/0001-*.md` + `design/high-level.md` and written to
`spec/kaggle-churn.md`, with `prd-hash` and `high-level-hash` pinned via
`git hash-object -w`. Nothing to reconcile — this is the baseline.

## Dataset

Registered a flat labeled table (no raw-logs build step needed):
`/Users/alex/dev/sandbox/data/playground-series-churn/train.csv` — the
full file, **100% of the 594,194-row source**, not a sample.

Split: stratified random 80/20 (`seed=42`, `test_share=0.20`), preserving
the observed `Churn` class balance in both halves. Random rather than
time-windowed because the label is a static snapshot with no timestamp
column and no stated horizon (see `design/high-level.md`'s ML framing) —
there is nothing to cut on. Seed and share match the monkey-mode
baseline's split so this step's numbers stay directly comparable to
`monkey-mode/report.md`'s.

Materialized to:
- `modeling/datasets/churn_train.csv` — 475,355 rows (train + this
  step's internal validation use)
- `modeling/datasets/churn_test.csv` — 118,839 rows (this project's
  *internal* held-out evaluation set, carved from `train.csv`)

This internal split is distinct from Kaggle's own unlabeled
`test.csv` (254,655 rows), which stays untouched and reserved for the
eventual competition submission — neither file here is that one.

Built by: `modeling/prepare_dataset.py` (registration + split + profile
in one small, re-runnable script).

## Profile (train split only, 475,355 rows x 21 columns, 123.8 MB)

**Nulls**: 0% across every column. No imputation was actually exercised.

**Target (`Churn`)**: `No` 77.48% (368,301 rows) / `Yes` 22.52%
(107,054 rows) — the same moderate imbalance observed in the full
dataset and in monkey-mode's split; no resampling or class weighting
applied at this step (that decision belongs to `ml-modeling-train`).

**Numeric features**:

| Feature | Min | Max | Mean | Median | Std | Skew |
|---|---|---|---|---|---|---|
| SeniorCitizen | 0.0 | 1.0 | 0.114 | 0.0 | 0.318 | 2.43 |
| tenure | 1.0 | 72.0 | 36.57 | 35.0 | 25.05 | 0.06 |
| MonthlyCharges | 18.25 | 118.75 | 65.89 | 74.15 | 31.08 | -0.29 |
| TotalCharges | 18.8 | 8684.8 | 2495.63 | 1434.65 | 2355.01 | 0.91 |

`SeniorCitizen` is a 0/1 flag, not a continuous quantity — its "skew"
number is an artifact of that binary shape, not a data-quality issue.
`tenure` and `MonthlyCharges` are close to symmetric; `TotalCharges` is
right-skewed as expected for a value that compounds tenure x charges.

**Categorical features**: 15 columns, cardinality 2-4 each (all
low-cardinality — full detail, including per-column top values, is in
`01-data.json`). `Contract` (Month-to-month 239,065 / Two year 149,440 /
One year 86,850) and `PaymentMethod` (Electronic check 172,165 / Credit
card auto 106,969 / Mailed check 99,011 / Bank transfer auto 97,210) are
the two flagged as strongest categorical signals in
`monkey-mode/report.md`.

## Quality flags

- **0 exact duplicate rows**, **0 duplicate `id` values** — table is
  clean on both counts.
- **No column exceeds 20% null rate** (every column sits at 0%) — no
  null-handling risk to carry forward.
- **`TotalCharges` vs. `tenure * MonthlyCharges` correlation: 0.9921** —
  confirms the near-redundancy `design/high-level.md`'s Phasing already
  flagged from monkey-mode's feature importances. This is a genuine,
  mechanically-expected relationship (not a data error), so nothing is
  changed here — it's a modeling decision for `ml-modeling-features`
  (keep all three vs. derive a cleaner ratio / drop one to reduce
  collinearity), not a cleaning one.
- **`id` leakage is still unverified** — carried forward unchanged from
  `design/high-level.md`'s open item, since checking predictive power of
  an id column is a feature-engineering question, not a null/duplicate/
  impossible-value cleaning question. No fix applied here; flagged for
  `ml-modeling-features`.

No `quality_flags` entry in this run crossed the impossible-vs-unusual
line into "fix it here" — nothing was masked, dropped, or imputed. The
profile above is the raw registered split, unmodified.

## Spec self-staleness

`spec/kaggle-churn.md`'s Testing Decisions section had a placeholder:
"Split rule: to be set by `ml-modeling-data`." Updated in place to: "Split
rule: stratified random 80/20, `seed=42`, `test_share=0.20`, carved from
the full `train.csv` (see `modeling/01-data.md` for reasoning)."

## Dashboard

`dashboard/eda.ipynb` built with real executed cells (shape, nulls,
target balance, numeric/categorical distributions — same facts as
above) via `nbformat`, executed with `jupyter nbconvert --execute
--inplace`. `dashboard/app.py` copied once from the shared
`assets/dashboard_app.py` template (never hand-edited per-project).
Streamlit launched in the background; port and URL reported in this
session's summary, recorded in `dashboard/.port` / `dashboard/.pid`.
