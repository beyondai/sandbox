# Train: Churn Prediction (minimal stand-in for dashboard verification)

Logistic Regression (`class_weight="balanced"`), standard-scaled numeric features + one-hot `plan_tier`, 80/20 stratified split, `random_state=0`. This is a minimal stand-in for verifying `ml-modeling-evaluate`'s new dashboard behavior — `ml-modeling-features`/`-train` were intentionally not run for this project per the dashboard verification scope (they're untouched by this change).
