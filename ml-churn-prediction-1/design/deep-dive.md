# Design Deep Dive: Churn Prediction

Backfilled Data section only, for verifying `ml-modeling-data`'s new EDA/dashboard behavior against the real dataset already generated for this project via monkey-mode (`monkey-mode/data.csv`). Features/Models/Training sections deliberately not filled in here — this project's real design work happened through monkey-mode, not the regular flow; this file exists only to satisfy `ml-modeling-*`'s required dependency for this verification run.

## Data

Real-time inference sources: not applicable — this is offline batch data for a modeling exercise, not a live-serving system.

Batch training sources: `monkey-mode/data.csv` — 600 rows, columns `tenure_months` (int), `monthly_usage_hours` (float), `plan_tier` (categorical: basic/standard/premium), `support_tickets_last_90d` (int), `payment_failures_last_90d` (int), `churned` (binary target, ~20% positive rate).

New data engineering: none — data already exists as a single flat CSV, no joins or pipeline work needed.
