"""Engineer features for the riot-churn v0 model.

Applied to train and test identically, using only rules fixed ahead of time
from the train profile in 01-data.md - nothing here is fit on data (no
mean/std, no learned categories), so applying the same code to test carries
no leakage even though test was never inspected to choose these rules.

Transforms, each justified by 01-data.md:
- region: null rate 29.5%, matches the raw source (a real "unknown" segment,
  not a bug) -> filled to the literal category "unknown" before one-hot,
  never imputed to a guessed region.
- platform, acquisition_source: low cardinality, straightforward one-hot.
- has_purchased: only 8.6% of scored players purchased pre-cutoff -> binary
  flag makes that sparsity an explicit signal instead of leaving it buried
  in skewed continuous columns.
- total_spend_log, purchase_count_log: skew 8.18 / 7.00 in 01-data.md ->
  log1p, replacing the raw columns (a linear model would otherwise be
  dominated by rare large values).
- total_party_games_log: skew 1.83 -> log1p, replacing the raw column.
- Other numeric features (active_days, total_games, total_wins,
  total_minutes, win_rate, days_since_last_active, activity_trend,
  tenure_at_scoring, days_since_last_purchase, distinct_item_types): skew is
  mild (<=0.83) or the domain is already tiny (distinct_item_types is 0-3) -
  left as raw values; scaling is deferred to the train step's pipeline, not
  done here.
- No time-based/cyclical features: no raw timestamp column exists in this
  table (day is already consumed by the aggregation in build_dataset.py).
- No target/frequency encoding: no high-cardinality categorical exists
  (max cardinality here is region at 4 known values + unknown).
- signup_day dropped: it is a deterministic linear transform of
  tenure_at_scoring (tenure = 120 - signup_day per build_dataset.py), so
  keeping both is pure duplicated information - confirmed by
  feature_selector.py scoring them almost identically (0.40 vs 0.27).
  tenure_at_scoring is kept as the more directly interpretable of the pair.
"""
import numpy as np
import pandas as pd

CATS = ["region", "platform", "acquisition_source"]


def engineer(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["region"] = df["region"].fillna("unknown")

    df["has_purchased"] = (df["purchase_count"] > 0).astype(int)
    df["total_spend_log"] = np.log1p(df["total_spend"])
    df["purchase_count_log"] = np.log1p(df["purchase_count"])
    df["total_party_games_log"] = np.log1p(df["total_party_games"])
    df = df.drop(
        columns=["total_spend", "purchase_count", "total_party_games", "signup_day"]
    )

    df = pd.get_dummies(df, columns=CATS, drop_first=True)
    return df


if __name__ == "__main__":
    train = pd.read_csv("datasets/churn_train.csv")
    test = pd.read_csv("datasets/churn_test.csv")

    train_f = engineer(train)
    test_f = engineer(test)
    # align columns (drop_first one-hot could in principle differ if a rare
    # category were missing from one split; not the case here, but keep the
    # tables aligned defensively)
    test_f = test_f.reindex(columns=train_f.columns, fill_value=0)

    train_f.to_csv("datasets/churn_train_features.csv", index=False)
    test_f.to_csv("datasets/churn_test_features.csv", index=False)

    print("train_f shape:", train_f.shape)
    print("test_f shape:", test_f.shape)
    print("columns:", list(train_f.columns))
