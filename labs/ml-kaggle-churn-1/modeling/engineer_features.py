"""Feature engineering for the churn train split.

Reads dataset.train only (never dataset.test - see ml-modeling-features).
Two deterministic, row-wise engineered features are added; everything
else stays raw for the training step's own encoding pipeline (one-hot on
low-cardinality categoricals, as decided here). `id` is dropped.

Both engineered functions below are pure/row-wise (no fit-on-train
statistic), so the same logic is safe to re-apply to the test split
later (in ml-modeling-train/-evaluate) with zero leakage risk - nothing
here was fit on train and needs a separate .transform() call.
"""

import pandas as pd

SOURCE = "datasets/churn_train.csv"
OUTPUT = "datasets/churn_train_features.csv"


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["TotalCharges_residual"] = df["TotalCharges"] - (
        df["tenure"] * df["MonthlyCharges"]
    )
    df["Contract_x_PaymentMethod"] = (
        df["Contract"] + "|" + df["PaymentMethod"]
    )
    return df


if __name__ == "__main__":
    df = pd.read_csv(SOURCE)
    df = add_engineered_features(df)
    df = df.drop(columns=["id"])
    df.to_csv(OUTPUT, index=False)
    print(f"wrote {OUTPUT}: {df.shape[0]} rows x {df.shape[1]} columns")
    print("columns:", list(df.columns))
