# Profile Data: Churn Prediction

## Profile

- **Shape**: 600 rows, 6 columns, 0.033 MB.
- **Nulls**: none in any column (0.0% across the board).
- **Target/label**: `churned`, binary classification, class balance 80.2% not-churned / 19.8% churned — imbalanced enough that accuracy alone would be misleading; lead with F1/precision-recall/AUC-ROC at modeling time.
- **Feature distributions**:
  - `tenure_months`: 1-60, mean 30.5, std 17.4, symmetric (skew ~0).
  - `monthly_usage_hours`: 0-51.8, mean 19.7, std 9.9, symmetric.
  - `support_tickets_last_90d`: 0-5, mean 1.0, std 0.98, mild right skew (0.96).
  - `payment_failures_last_90d`: 0-2, mean 0.27, std 0.50, notably right-skewed (1.72) — most rows are 0, a small tail has 1-2 failures.
  - `plan_tier` (categorical, cardinality 3): basic 39.2%, standard 39.0%, premium 21.8%.
- **Quality flags**: `payment_failures_last_90d` is highly skewed — worth a log or binary ("had any failure") transform in feature engineering rather than using it raw. No nulls, no duplicate rows, no other quality issues.

Done: every number above is computed from the real 600-row dataset (`monkey-mode/data.csv`), matching `modeling/01-data.json`.
