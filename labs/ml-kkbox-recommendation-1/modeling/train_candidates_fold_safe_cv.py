"""Fold-safe re-run of the 3-candidate CV comparison.

The first pass (modeling/train-candidates/*/train.py, each written by a
separate subagent) computed msno_repeat_rate_loo, song_repeat_rate_loo, and
artist_repeat_rate_loo ONCE across the full training table, then ran 5-fold
CV on the already-built table. That's a real leakage bug: a validation
fold's row still had its aggregate feature built partly from OTHER rows of
the same user/song/artist that also sit in that same validation fold (LOO
only excludes a row's own label, not its whole fold). HistGradientBoosting
exploited this far more than Random Forest or Logistic Regression could
(CV AUC 0.936 vs 0.755 vs 0.736 - an implausible gap for this task, whose
public leaderboard tops out around 0.72-0.74).

Fix: for each of the 5 folds, recompute those three aggregate features from
ONLY that fold's training rows (leave-one-out within the fold's train
portion for fitting; plain smoothed mean via left-join, from the same
fold's train portion, applied to that fold's validation portion - this is
exactly the "Applying to the test split" methodology in 02-features.md,
just run once per fold instead of once at the real train/test boundary).
All other 106 columns in kkbox_train_features.csv don't depend on the
target column at all (one-hot, frequency-of-value encodings, date/log
transforms) - no fold-crossing leakage risk for those, reused as-is.
"""

import time
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RAW_PATH = "modeling/datasets/kkbox_train.csv"
FEAT_PATH = "modeling/datasets/kkbox_train_features.csv"
SMOOTHING_K = 10
SEED = 42

LEAKY_COLS = [
    "msno_repeat_rate_loo", "msno_count",
    "song_repeat_rate_loo", "song_count",
    "artist_repeat_rate_loo", "artist_count",
]
ENTITIES = [("msno", "msno"), ("song_id", "song"), ("artist_name", "artist")]


def fold_safe_entity_features(train_df, val_df, key, prefix, global_mean):
    key_train = train_df[key].fillna("missing")
    key_val = val_df[key].fillna("missing")

    grp = train_df.groupby(key_train)["target"]
    count = grp.transform("count")
    total = grp.transform("sum")
    others_count = count - 1
    others_sum = total - train_df["target"]
    loo = (others_sum + SMOOTHING_K * global_mean) / (others_count + SMOOTHING_K)

    lookup = (
        key_train.to_frame(key)
        .join(train_df["target"])
        .groupby(key)["target"]
        .agg(count="count", sum_="sum")
        .reset_index()
    )
    lookup["rate"] = (lookup["sum_"] + SMOOTHING_K * global_mean) / (
        lookup["count"] + SMOOTHING_K
    )

    val_join = key_val.to_frame(key).merge(
        lookup[[key, "rate", "count"]], on=key, how="left"
    )
    val_join["rate"] = val_join["rate"].fillna(global_mean)
    val_join["count"] = val_join["count"].fillna(0)

    return (
        loo.to_numpy(), count.to_numpy(),
        val_join["rate"].to_numpy(), val_join["count"].to_numpy(),
    )


def build_model(name):
    if name == "logistic_regression":
        return Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, random_state=SEED)),
        ])
    if name == "random_forest":
        return Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("clf", RandomForestClassifier(
                n_estimators=200, max_depth=12, random_state=SEED, n_jobs=4
            )),
        ])
    if name == "hist_gradient_boosting":
        return HistGradientBoostingClassifier(random_state=SEED, max_iter=200)
    raise ValueError(name)


def main():
    raw = pd.read_csv(RAW_PATH)[["row_id", "msno", "song_id", "artist_name"]]
    feat = pd.read_csv(FEAT_PATH).drop(columns=LEAKY_COLS)
    df = raw.merge(feat, on="row_id", how="inner")
    assert len(df) == len(feat), "merge dropped/duplicated rows"

    y = df["target"]
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

    model_names = ["logistic_regression", "random_forest", "hist_gradient_boosting"]
    fold_scores = {name: [] for name in model_names}
    t0 = time.time()

    for fold_i, (tr_idx, va_idx) in enumerate(skf.split(df, y)):
        train_df = df.iloc[tr_idx].reset_index(drop=True)
        val_df = df.iloc[va_idx].reset_index(drop=True)
        global_mean = train_df["target"].mean()

        train_extra, val_extra = {}, {}
        for key, prefix in ENTITIES:
            loo, count_tr, rate_va, count_va = fold_safe_entity_features(
                train_df, val_df, key, prefix, global_mean
            )
            train_extra[f"{prefix}_repeat_rate_loo"] = loo
            train_extra[f"{prefix}_count"] = count_tr
            val_extra[f"{prefix}_repeat_rate_loo"] = rate_va
            val_extra[f"{prefix}_count"] = count_va

        drop_cols = ["row_id", "msno", "song_id", "artist_name", "target"]
        X_train = train_df.drop(columns=drop_cols).copy()
        X_val = val_df.drop(columns=drop_cols).copy()
        for k, v in train_extra.items():
            X_train[k] = v
        for k, v in val_extra.items():
            X_val[k] = v
        y_train, y_val = train_df["target"], val_df["target"]

        for name in model_names:
            model = clone(build_model(name))
            fold_t0 = time.time()
            model.fit(X_train, y_train)
            probs = model.predict_proba(X_val)[:, 1]
            auc = roc_auc_score(y_val, probs)
            fold_scores[name].append(auc)
            print(f"fold {fold_i} {name}: auc={auc:.4f} "
                  f"({time.time()-fold_t0:.1f}s)", flush=True)

    total_time = time.time() - t0
    print(f"\ntotal wall time: {total_time:.1f}s\n")

    results = {}
    for name in model_names:
        scores = np.array(fold_scores[name])
        results[name] = {
            "cv_auc_mean_fold_safe": round(float(scores.mean()), 4),
            "cv_auc_std_fold_safe": round(float(scores.std()), 4),
            "fold_scores": [round(float(s), 4) for s in scores],
        }
        print(name, results[name])

    import json
    with open("modeling/fold_safe_cv_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
