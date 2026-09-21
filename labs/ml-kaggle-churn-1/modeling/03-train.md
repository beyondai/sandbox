# Modeling Step 3 — Train (Quick POC, sequential)

No mode keyword in this request. Continuing Quick POC to match this
project's established pace. Request named "2 models" — read as: use
this sequential skill's own CV-based comparison (the algorithm
selection section already calls for "cross-validation, not a single
split, to pick between candidates") to compare exactly 2 candidates,
then train and record the winner as the single chosen candidate — not a
request to switch to `ml-modeling-multiagent`, which wasn't named and
which this run didn't use (no concurrent subagents, no
`train-candidates/` directory).

Design docs changed? `prd/kaggle-churn.md` and `design/high-level.md`
hashes still match `spec/kaggle-churn.md`'s pinned hashes. Proceeding.

Input: `02-features.md`'s Output table,
`modeling/datasets/churn_train_features.csv` (475,355 rows x 22
columns). `dataset.test` (`churn_test.csv`) was never read in this step.

## Candidates (from `design/high-level.md`'s Phasing V1)

Phasing V1 named exactly this comparison: "Compare the baseline
RandomForest against one gradient-boosted-tree candidate ... under
proper cross-validation instead of a single split."

- **`random_forest`**: matches the algorithm-selection matrix's "Small
  data (<10K rows)" starting point and is also what the V0 monkey-mode
  baseline already used — kept as the control candidate to measure the
  V1 upgrade against.
- **`hist_gradient_boosting`** (`sklearn.ensemble
  .HistGradientBoostingClassifier`): fills the matrix's "Medium data,
  high accuracy needed -> XGBoost/LightGBM" workhorse row. Chose
  scikit-learn's own histogram GBM over adding `xgboost`/`lightgbm` as
  new dependencies — same algorithm family (histogram-binned gradient
  boosting), already in the shared venv, no `uv add` needed.

No third candidate (e.g. logistic regression) was tried: interpretability
isn't a requirement per the PRD, so the matrix's "Interpretability
required" row doesn't apply here.

## Leakage / per-fold nesting check

Neither engineered feature in `02-features.md` (`TotalCharges_residual`,
`Contract_x_PaymentMethod`) is a target-derived aggregate — both are
pure row-wise functions of other feature columns, computed once, with no
leave-one-out or target-encoded statistic involved. The per-fold-nesting
warning in `ml-modeling-features` doesn't apply; this run's CV ranking
is trustworthy as-is, not provisional.

## Class imbalance handling

`01-data.md`: 77.48% No / 22.52% Yes (moderate imbalance). Used
`class_weight="balanced"` on both candidates (scikit-learn's built-in
inverse-frequency reweighting) rather than resampling — cheaper, no
synthetic rows, and this skill's own guidance is class weights first,
resampling only if weights underperform. Not revisited here since both
candidates trained cleanly with weighting; resampling was never tried.

## Quick POC time budget (stated explicitly, not silent)

- **3-fold CV**, not Regular's 5-fold.
- `RandomForestClassifier(n_estimators=100, max_depth=12)` — half
  Regular's 200 trees, `max_depth=12` (kept, following the example
  numbers in `ml-modeling-train`'s own time-budget section).
- `HistGradientBoostingClassifier(max_iter=100)` — half Regular's 200
  iterations.
- Both `random_state=42`, `StratifiedKFold(n_splits=3, shuffle=True,
  random_state=42)`.
- No feature scaling in the pipeline — both candidates are tree-based
  and monotonic-transform-invariant (see `02-features.md`); only
  `OneHotEncoder` on the 16 categorical columns (15 original +
  `Contract_x_PaymentMethod`), numeric columns passed through raw.

## Implementation

The actual script that ran (`modeling/train.py`, executed via
`uv run python3 train.py`):

```python
preprocess = ColumnTransformer(
    transformers=[
        ("num", "passthrough", numeric_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
    ]
)

candidates = {
    "random_forest": RandomForestClassifier(
        n_estimators=100, max_depth=12, class_weight="balanced",
        n_jobs=-1, random_state=42,
    ),
    "hist_gradient_boosting": HistGradientBoostingClassifier(
        max_iter=100, class_weight="balanced", random_state=42,
    ),
}

cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
for name, model in candidates.items():
    pipeline = Pipeline(steps=[("preprocess", preprocess), ("model", model)])
    scores = cross_val_score(pipeline, X, y, cv=cv, scoring="roc_auc")
    # ... record mean/std/elapsed

winner_name = max(results, key=lambda k: results[k]["cv_roc_auc_mean"])
winner_pipeline.fit(X, y)  # final fit on the full train table
joblib.dump({"pipeline": winner_pipeline, "winner_name": winner_name},
            "model.joblib")
```

Full script at `modeling/train.py`; raw CV results at
`modeling/03-train_cv_results.json`; experiment log at
`modeling/experiments.json`.

## Results

| Candidate | CV ROC-AUC (mean) | std | Wall-clock (3-fold CV) |
|---|---|---|---|
| random_forest | 0.9121 | 0.0007 | 31.2s |
| hist_gradient_boosting | **0.9148** | 0.0007 | 18.4s |

Total run (both candidates' CV + final fit): ~60s, comfortably under the
3-minute Quick POC budget.

**Winner: `hist_gradient_boosting`** — higher mean CV ROC-AUC (0.9148 vs
0.9121), a real if modest gap given both folds' std is 0.0007 (the gap
is ~4 std devs, not noise), and it also ran faster (18.4s vs 31.2s for
CV). Both candidates already beat monkey-mode's single-split baseline
(0.9049) — expected, since this run adds the engineered features
(`Contract_x_PaymentMethod` in particular, validated at mutual_info
0.3179 in `02-features.md`), class weighting, and proper cross-validated
estimation instead of one split.

Final winner pipeline fit on the full 475,355-row train-features table
in 7.5s, saved to `modeling/model.joblib` (dict with `pipeline` and
`winner_name` keys) for `ml-modeling-evaluate` to load and score against
the held-out `churn_test.csv` split.

## Spec self-staleness

`spec/kaggle-churn.md`'s Implementation Decisions section already named
the V1 comparison ("compare a GBM candidate under cross-validation") as
a plan, not a placeholder needing a literal value substituted — no
contradiction to reconcile. No spec edit needed.
