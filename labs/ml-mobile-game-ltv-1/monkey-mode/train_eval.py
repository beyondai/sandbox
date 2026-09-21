"""
Train and evaluate the fast baseline for ltv_d8_d180 regression.

Loads the per-user feature table produced by aggregate_features.py,
does an 80/20 random split, standard-scales numerics + one-hot encodes
low-cardinality categoricals, trains a single HistGradientBoostingRegressor
(no hyperparameter search), and reports RMSE against two baselines:
predict-zero and predict-train-mean.
"""
import json

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RANDOM_STATE = 42

df = pd.read_parquet("user_features.parquet")

CATEGORICAL = ["platform", "country_tier", "channel_tier"]
NUMERIC = [
    "install_day", "install_week",
    "n_events", "n_sessions",
    "n_iap", "iap_revenue_total", "iap_revenue_mean",
    "n_ad_impressions", "ad_revenue_total", "ad_revenue_mean",
    "days_active", "sessions_d0_2", "sessions_d3_5", "sessions_d6_7",
    "n_distinct_networks", "n_distinct_placements",
    "event_hour_mean", "event_hour_std",
    "total_revenue_d0_7", "is_payer_d0_7",
]
FEATURES = CATEGORICAL + NUMERIC
TARGET = "ltv_d8_d180"

X = df[FEATURES]
y = df[TARGET].astype("float64")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_STATE
)

preprocess = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ("num", StandardScaler(), NUMERIC),
    ]
)

model = Pipeline(steps=[
    ("preprocess", preprocess),
    ("gbr", HistGradientBoostingRegressor(random_state=RANDOM_STATE)),
])

model.fit(X_train, y_train)
pred = model.predict(X_test)
pred = np.clip(pred, 0, None)  # revenue can't be negative

rmse_model = root_mean_squared_error(y_test, pred)

# Baselines
pred_zero = np.zeros_like(y_test)
rmse_zero = root_mean_squared_error(y_test, pred_zero)

train_mean = y_train.mean()
pred_mean = np.full_like(y_test, train_mean)
rmse_mean = root_mean_squared_error(y_test, pred_mean)

# log1p-space RMSE (context metric, on the skewed target)
rmse_log1p_model = root_mean_squared_error(np.log1p(y_test), np.log1p(pred))
rmse_log1p_zero = root_mean_squared_error(np.log1p(y_test), np.log1p(pred_zero))
rmse_log1p_mean = root_mean_squared_error(np.log1p(y_test), np.log1p(pred_mean))

# payer vs non-payer split (on true d8-180 outcome, test set)
is_payer_outcome = y_test > 0
rmse_model_payers = root_mean_squared_error(
    y_test[is_payer_outcome], pred[is_payer_outcome]
) if is_payer_outcome.sum() else float("nan")
rmse_model_nonpayers = root_mean_squared_error(
    y_test[~is_payer_outcome], pred[~is_payer_outcome]
) if (~is_payer_outcome).sum() else float("nan")

results = {
    "n_train": len(X_train),
    "n_test": len(X_test),
    "train_mean_target": float(train_mean),
    "rmse_model_usd": float(rmse_model),
    "rmse_predict_zero_usd": float(rmse_zero),
    "rmse_predict_mean_usd": float(rmse_mean),
    "rmse_model_log1p": float(rmse_log1p_model),
    "rmse_predict_zero_log1p": float(rmse_log1p_zero),
    "rmse_predict_mean_log1p": float(rmse_log1p_mean),
    "pct_test_users_nonzero_outcome": float(is_payer_outcome.mean()),
    "rmse_model_payers_usd": float(rmse_model_payers),
    "rmse_model_nonpayers_usd": float(rmse_model_nonpayers),
}

with open("results.json", "w") as f:
    json.dump(results, f, indent=2)

print(json.dumps(results, indent=2))
