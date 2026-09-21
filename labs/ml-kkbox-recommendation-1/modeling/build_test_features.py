"""Build the test-split feature table, per 02-features.md's "Applying to
the test split" section. Never opened until this step (ml-modeling-evaluate)
- test rows were never part of any training aggregate, so left-joining the
train-derived lookup tables here is leakage-free.

Writes modeling/datasets/kkbox_test_features.csv, with the exact same
column set (order matters less, but presence does) as
modeling/datasets/kkbox_train_features.csv minus row_id/target, so the
trained model can score it directly.
"""

import numpy as np
import pandas as pd

TEST_PATH = "modeling/datasets/kkbox_test.csv"
TRAIN_FEATURES_PATH = "modeling/datasets/kkbox_train_features.csv"
OUT_DIR = "modeling/datasets"

LOW_CARD_CATS = [
    "source_system_tab", "source_screen_name", "source_type",
    "city", "gender", "registered_via", "language",
]


def main():
    df = pd.read_csv(TEST_PATH)
    train_cols = pd.read_csv(TRAIN_FEATURES_PATH, nrows=0).columns.tolist()
    out = pd.DataFrame({"row_id": df["row_id"], "target": df["target"]})

    # --- Leave-one-out repeat rates -> plain left-join from train-derived
    # lookups (no leave-one-out for test rows: they were never part of the
    # training aggregate, so the full-train smoothed mean is leakage-free).
    for key, prefix, lookup_file in [
        ("msno", "msno", "msno_repeat_rate.csv"),
        ("song_id", "song", "song_repeat_rate.csv"),
        ("artist_name", "artist", "artist_repeat_rate.csv"),
    ]:
        lookup = pd.read_csv(f"{OUT_DIR}/{lookup_file}")
        global_mean_fallback = (lookup["rate"] * lookup["count"]).sum() / lookup["count"].sum()
        key_filled = df[key].fillna("missing")
        joined = key_filled.to_frame(key).merge(lookup, on=key, how="left")
        out[f"{prefix}_repeat_rate_loo"] = joined["rate"].fillna(global_mean_fallback)
        out[f"{prefix}_count"] = joined["count"].fillna(0)

    # --- bd + bd_missing: identical to build_features.py, no lookup needed ---
    out["bd"] = df["bd"]
    out["bd_missing"] = df["bd"].isna().astype(int)

    # --- song_length_log: deterministic, no lookup needed ---
    out["song_length_log"] = np.log1p(df["song_length"])

    # --- membership_duration_days: deterministic, no lookup needed ---
    reg = pd.to_datetime(df["registration_init_time"], format="%Y%m%d")
    exp = pd.to_datetime(df["expiration_date"], format="%Y%m%d")
    out["membership_duration_days"] = (exp - reg).dt.days

    # --- Low-cardinality one-hot: recompute, then align to train's columns ---
    for col in LOW_CARD_CATS:
        filled = df[col].astype("object").fillna("missing").astype(str)
        dummies = pd.get_dummies(filled, prefix=col, dtype=int)
        out = pd.concat([out, dummies], axis=1)

    # --- Combined context frequency: recompute string, left-join lookup ---
    context_lookup = pd.read_csv(f"{OUT_DIR}/context_freq.csv")
    context = (
        df["source_system_tab"].fillna("missing").astype(str) + "|"
        + df["source_screen_name"].fillna("missing").astype(str) + "|"
        + df["source_type"].fillna("missing").astype(str)
    )
    context_joined = context.to_frame("source_context").merge(
        context_lookup, on="source_context", how="left"
    )
    out["source_context_freq"] = context_joined["freq"].fillna(0)

    # --- artist_name_freq: left-join lookup ---
    artist_freq_lookup = pd.read_csv(f"{OUT_DIR}/artist_freq.csv")
    artist_filled = df["artist_name"].fillna("missing")
    artist_joined = artist_filled.to_frame("artist_name").merge(
        artist_freq_lookup, on="artist_name", how="left"
    )
    out["artist_name_freq"] = artist_joined["freq"].fillna(0)

    # --- genre_primary one-hot: recompute, map non-top-15 to "other",
    # align to train's exact column set ---
    # dtype=str forced on read: the CSV's bare digit strings ("465") would
    # otherwise be inferred as int64, silently breaking .isin() against the
    # string-typed genre_primary column below (found via a real bug: every
    # test row fell into "other" because "465" != 465).
    top_genres = pd.read_csv(
        f"{OUT_DIR}/genre_primary_top.csv", dtype={"genre_primary": str}
    )["genre_primary"].tolist()
    genre_primary = df["genre_ids"].astype(str).str.split("|").str[0]
    genre_primary_top = genre_primary.where(genre_primary.isin(top_genres), "other")
    genre_dummies = pd.get_dummies(genre_primary_top, prefix="genre_primary", dtype=int)
    out = pd.concat([out, genre_dummies], axis=1)

    # --- Align to train's exact column set: a category unseen in test
    # needs its all-zero column added; extra test-only categories (shouldn't
    # happen here since these are all one-hot over fixed reference lists,
    # but check) get dropped with a note. ---
    missing_cols = [c for c in train_cols if c not in out.columns]
    for c in missing_cols:
        out[c] = 0
    extra_cols = [c for c in out.columns if c not in train_cols]
    if extra_cols:
        print(f"WARNING dropping test-only columns not seen in train: {extra_cols}")
        out = out.drop(columns=extra_cols)
    out = out[train_cols]  # exact same order as train

    out.to_csv(f"{OUT_DIR}/kkbox_test_features.csv", index=False)
    print(f"rows={len(out)} cols={out.shape[1]}")
    print(f"missing_cols_filled_zero={missing_cols}")


if __name__ == "__main__":
    main()
