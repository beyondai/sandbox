"""
Monkey-mode fast baseline: subscriber churn prediction.

End-to-end script: synthetic data generation -> cleaning -> feature prep ->
model training -> held-out evaluation. Deliberately minimal (single model,
single split, no tuning) per "monkey mode" scope.
"""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 42
N_ROWS = 600

# ---------------------------------------------------------------------------
# 1. Synthetic data generation
# ---------------------------------------------------------------------------
rng = np.random.default_rng(SEED)

tenure_months = rng.integers(1, 61, size=N_ROWS)  # 1-60 months
monthly_usage_hours = np.clip(rng.normal(loc=20, scale=10, size=N_ROWS), 0, None)
plan_tier = rng.choice(["basic", "standard", "premium"], size=N_ROWS, p=[0.4, 0.4, 0.2])
support_tickets_last_90d = rng.poisson(lam=1.0, size=N_ROWS)
payment_failures_last_90d = rng.poisson(lam=0.3, size=N_ROWS)

# Build churn probability from a linear combination of signal features, then
# sample the binary label from it (logistic link) so the label genuinely
# depends on the features rather than being random noise:
#   - more tenure and more usage hours push churn probability down
#   - more support tickets and more payment failures push it up
#   - cheaper plans (basic) churn a bit more than premium
plan_tier_effect = pd.Series(plan_tier).map({"basic": 0.3, "standard": 0.0, "premium": -0.3}).to_numpy()

logit = (
    -1.6
    - 0.05 * tenure_months
    - 0.06 * monthly_usage_hours
    + 1.2 * support_tickets_last_90d
    + 2.6 * payment_failures_last_90d
    + plan_tier_effect
)
churn_prob = 1 / (1 + np.exp(-logit))
churned = rng.binomial(1, churn_prob)

df = pd.DataFrame(
    {
        "tenure_months": tenure_months,
        "monthly_usage_hours": monthly_usage_hours.round(2),
        "plan_tier": plan_tier,
        "support_tickets_last_90d": support_tickets_last_90d,
        "payment_failures_last_90d": payment_failures_last_90d,
        "churned": churned,
    }
)

data_path = "data.csv"
df.to_csv(data_path, index=False)

print(f"Generated {len(df)} rows, churn rate = {df['churned'].mean():.3f}")

# ---------------------------------------------------------------------------
# 2. Cleaning (fast defaults: drop/median-impute nulls -- none expected here)
# ---------------------------------------------------------------------------
print("Null counts:\n", df.isnull().sum())
df = df.fillna(df.median(numeric_only=True))

# ---------------------------------------------------------------------------
# 3. Features: standard-scale numeric, one-hot encode plan_tier
# ---------------------------------------------------------------------------
numeric_features = [
    "tenure_months",
    "monthly_usage_hours",
    "support_tickets_last_90d",
    "payment_failures_last_90d",
]
categorical_features = ["plan_tier"]

X = df[numeric_features + categorical_features]
y = df["churned"]

preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
    ]
)

# ---------------------------------------------------------------------------
# 4. Model: single Logistic Regression, trained once (class_weight="balanced"
# to account for the ~20% minority churn class). Chosen over a random forest
# because the label-generating process here is itself a logistic function of
# the features, so a linear model is well matched to the signal and is the
# faster, simpler fast-default choice.
# ---------------------------------------------------------------------------
model = Pipeline(
    steps=[
        ("preprocess", preprocessor),
        ("clf", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=SEED)),
    ]
)

# ---------------------------------------------------------------------------
# 5. Eval: 80/20 held-out split, random_state=0
# ---------------------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=0, stratify=y
)

model.fit(X_train, y_train)
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, zero_division=0)
recall = recall_score(y_test, y_pred, zero_division=0)
f1 = f1_score(y_test, y_pred, zero_division=0)

print("\n=== Held-out test metrics (80/20 split, random_state=0) ===")
print(f"Accuracy:  {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1:        {f1:.4f}")
