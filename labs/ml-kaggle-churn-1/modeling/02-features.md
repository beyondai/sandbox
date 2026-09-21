# Modeling Step 2 — Features (Quick POC)

No mode keyword in this request. Continuing Quick POC to match this
project's established pace — picks the most obviously useful transforms
and moves on, backed by `feature_selector.py` evidence rather than
exhaustive comparison.

Design docs changed? `prd/kaggle-churn.md` and `design/high-level.md`
hashes still match `spec/kaggle-churn.md`'s pinned `prd-hash`/
`high-level-hash`. Proceeding.

Input: `01-data.json` -> `dataset.train`
(`modeling/datasets/churn_train.csv`) only. `dataset.test`
(`churn_test.csv`) was never opened in this step.

## Feature list

**Dropped**: `id`. `design/high-level.md` and `monkey-mode/report.md`
both carried this as an unverified assumption ("dropped without testing
it"). Resolved here with evidence:
`feature_selector.py --file datasets/churn_train.csv --target Churn`
gives `id` a composite score of 0.4084 (5th of 20 raw columns), but that
score is inflated entirely by its variance/cardinality sub-scores
(`variance: 0.577`, from 475,355 unique values) — its `mutual_info` with
`Churn` is **0.0002**, roughly 200x lower than the weakest real feature
(`SeniorCitizen` at 0.0448). This is the same trap a naive top-N read of
the composite score would have missed: high cardinality inflates the
score without any real relationship to the target. `id` is dropped from
the output table.

**Numeric, kept raw** (no log/sqrt/squared/binned transforms applied):
`SeniorCitizen`, `tenure`, `MonthlyCharges`, `TotalCharges`. Skipped the
transform menu because both model candidates named in
`design/high-level.md`'s Phasing V1 (RandomForest, a GBM) are tree-based
and invariant to monotonic transforms of numeric inputs — log/sqrt/
squared/binned would change nothing for either candidate. Also skipped
missing-value indicator flags (0% null rate on every column per
`01-data.md` — nothing to flag) and quantile binning for `TotalCharges`
(same tree-invariance reasoning, plus binning would discard granularity
a tree can use directly).

**Categorical, one-hot at train time** (all low-cardinality, 2-4 values
each, per `01-data.md`): `gender`, `Partner`, `Dependents`,
`PhoneService`, `MultipleLines`, `InternetService`, `OnlineSecurity`,
`OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`,
`StreamingMovies`, `Contract`, `PaperlessBilling`, `PaymentMethod`.
Target/frequency encoding was skipped — no categorical here is
high-cardinality (the only high-cardinality column was `id`, now
dropped entirely rather than encoded).

**Engineered - interaction/cross features**:

- `TotalCharges_residual = TotalCharges - (tenure * MonthlyCharges)`.
  Justified by `01-data.md`'s profile evidence: `TotalCharges` correlates
  with `tenure * MonthlyCharges` at 0.9921, not exactly 1.0, implying a
  small non-mechanical remainder (rate changes, promotions, etc.) the
  three raw columns don't expose directly. Selector result after adding
  it: composite score 0.5429, but `mutual_info` only **0.0096** — weaker
  standalone signal than any of the three raw numerics it's built from.
  Kept anyway (cheap, harmless for a tree ensemble to ignore if useless)
  but the file records this honestly as a low-confidence addition for
  `ml-modeling-train` to confirm or discard via feature importance, not
  a validated win.
- `Contract_x_PaymentMethod` (string concat, `"<Contract>|<PaymentMethod>"`,
  cardinality 12, one-hot at train time). Justified by
  `monkey-mode/report.md`: `Contract_Month-to-month` and
  `PaymentMethod_Electronic check` both independently rank in the top 5
  feature importances there, suggesting a possible compounding effect
  neither column alone fully captures. Selector confirms real added
  value: `mutual_info` **0.3179**, higher than either parent column alone
  (`Contract` 0.2496, `PaymentMethod` 0.2101) — this one earned its spot,
  unlike the residual above.

**Not applied, with reasons** (tried-and-dropped, not silently skipped):

- Leave-one-out aggregation features: not applicable. The framing's unit
  of prediction is one row per customer (`design/high-level.md`), and
  `01-data.md` confirms 0 duplicate `id` values — no repeated-entity
  structure exists to aggregate a per-entity historical stat over.
- Embeddings: skipped per this family's Quick-POC default — no free-text
  or high-cardinality ID column left that would benefit from one (`id`
  was dropped, not encoded).
- Cheap text signals: skipped — no free-text column in this dataset.
- Time-based/cyclical encoding: skipped — no datetime column;
  `tenure` is an integer month count, not a timestamp.

## Output table

`modeling/datasets/churn_train_features.csv` — 475,355 rows x 22 columns
(20 original feature columns minus `id`, plus `Churn`,
`TotalCharges_residual`, `Contract_x_PaymentMethod`). Built by
`modeling/engineer_features.py`, a small re-runnable script; both
engineered columns are pure row-wise functions (no train-fitted
statistic), so `ml-modeling-train`/`-evaluate` can re-apply the same
`add_engineered_features()` function to the `churn_test.csv` split
later with zero leakage risk - this step did not touch `dataset.test`
itself, per the input rule above.

## Selection

`feature_selector.py` run twice: once against the raw train split
(pre-engineering, justifying the `id` drop) and once against
`churn_train_features.csv` (post-engineering, justifying both new
columns). Full rankings and per-feature `scores` breakdown (mutual_info,
variance, cardinality, null_completeness) are reproducible via:

```
python3 ../../.agents/skills/personal/ml-modeling/scripts/feature_selector.py \
  --file datasets/churn_train_features.csv --target Churn --json
```

## Spec self-staleness

`spec/kaggle-churn.md`'s Solution section stated: "Known open exclusion:
whether `id` itself carries leakage is unverified, deferred to feature
engineering." Updated in place to: "`id` was tested and dropped —
`mutual_info` with `Churn` is 0.0002 (see `modeling/02-features.md`),
confirming it carries no real signal; excluded from the feature set."
