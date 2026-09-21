"""Engineer features for the KKBOX repeat-listen POC.

Reads modeling/datasets/kkbox_train.csv (train split only - test is never
opened here, per this step's scope). Writes:
  - modeling/datasets/kkbox_train_features.csv   (the Output table)
  - modeling/datasets/msno_repeat_rate.csv        (lookup: msno -> smoothed rate, count)
  - modeling/datasets/song_repeat_rate.csv        (lookup: song_id -> smoothed rate, count)
  - modeling/datasets/artist_repeat_rate.csv      (lookup: artist_name -> smoothed rate, count)
  - modeling/datasets/artist_freq.csv             (lookup: artist_name -> freq)
  - modeling/datasets/genre_primary_top.csv       (the top-15 genre ids kept as one-hot levels)
  - modeling/datasets/context_freq.csv            (lookup: tab|screen|type -> freq)

The lookup tables are needed again at evaluate time: they must be
LEFT-JOINED (not leave-one-out) onto the held-out test split before scoring,
since test rows were never part of the training aggregate - see
02-features.md, "Applying to the test split".

Design driven by design/high-level.md's framing, modeling/01-data.md's
profile/risk flags, and monkey-mode/report.md's baseline learnings - see
02-features.md for the reasoning behind each choice below, including two
ideas from the first pass that were dropped/fixed on review: `isrc_country`
(redundant with `language`, dropped) and `genre_primary_freq` (frequency
encoding collapsed distinct genres of similar popularity into the same
value - replaced with one-hot top-15 + other).
"""

import numpy as np
import pandas as pd

IN_PATH = "modeling/datasets/kkbox_train.csv"
OUT_DIR = "modeling/datasets"
SMOOTHING_K = 10  # shrinkage strength toward the global mean - see 02-features.md

LOW_CARD_CATS = [
    "source_system_tab", "source_screen_name", "source_type",
    "city", "gender", "registered_via", "language",
]


def main():
    df = pd.read_csv(IN_PATH)
    out = pd.DataFrame({"row_id": df["row_id"], "target": df["target"]})
    global_mean = df["target"].mean()

    # --- Smoothed, leave-one-out historical repeat-listen rate, per user,
    # per song, and per artist ---
    # monkey-mode's top-15 feature importances were dominated by listening
    # context; per-entity history was flagged in its Suggested Next Steps as
    # the natural next group to try but out of scope there. Leave-one-out
    # (exclude the row's own target) is mandatory: each row is one
    # (user, song) pair, so a plain group mean would encode the row's own
    # label directly into its own feature - that's target leakage, not a
    # subtler timing leak.
    #
    # First pass used a raw LOO rate with a single fallback for count==1
    # groups (fillna(global_mean)). On review that's a bad idea past
    # count==1 too: a count==2 group's LOO rate is either 0% or 100% from a
    # single other observation - extremely noisy, not usefully different
    # from "unknown." Replaced with count-weighted shrinkage toward the
    # global mean (k=10, i.e. a group needs roughly 10 observations before
    # its own rate is trusted over the global average) - this also removes
    # the separate count==1 special case, since the formula degrades to
    # exactly global_mean when count-1 is 0.
    # NaN keys need an explicit fill before grouping: pandas groupby drops
    # NaN groups entirely by default, which would silently produce NaN in
    # every downstream column for those rows (found via a real bug: 17 rows
    # have NaN artist_name - a songs.csv join gap, same 17 rows as
    # song_length's NaN - and without this fill they'd get NaN
    # artist_repeat_rate_loo/artist_count too, inconsistent with how every
    # other categorical column here handles missingness explicitly).
    entities = [("msno", "msno"), ("song_id", "song"), ("artist_name", "artist")]
    for key, prefix in entities:
        key_series = df[key].fillna("missing")
        grp = df.groupby(key_series)["target"]
        count = grp.transform("count")
        total = grp.transform("sum")
        others_count = count - 1
        others_sum = total - df["target"]
        smoothed_loo = (others_sum + SMOOTHING_K * global_mean) / (
            others_count + SMOOTHING_K
        )
        out[f"{prefix}_repeat_rate_loo"] = smoothed_loo
        out[f"{prefix}_count"] = count

        # Lookup for the test split: same smoothing, but over the FULL
        # group (no leave-one-out) - test rows were never part of the
        # training aggregate, so a plain smoothed mean is leakage-free.
        full = key_series.to_frame(key).join(df["target"]).groupby(key)["target"] \
            .agg(count="count", sum_="sum").reset_index()
        full["rate"] = (full["sum_"] + SMOOTHING_K * global_mean) / (
            full["count"] + SMOOTHING_K
        )
        full[[key, "rate", "count"]].to_csv(
            f"{OUT_DIR}/{prefix}_repeat_rate.csv", index=False
        )

    # --- bd: already cleaned to null for invalid values in build_dataset.py.
    # Add a missing-flag; leave imputation/scaling to the train step's own
    # pipeline (same division of labor monkey-mode used: engineer/flag here,
    # impute+scale in the model pipeline) so the feature table stays
    # imputation-strategy-agnostic.
    out["bd"] = df["bd"]
    out["bd_missing"] = df["bd"].isna().astype(int)

    # --- song_length: log1p per 01-data.md's flagged skew (17.32) ---
    out["song_length_log"] = np.log1p(df["song_length"])

    # --- membership_duration_days: derived from the two YYYYMMDD-int date
    # columns (01-data.md notes neither is meaningful as a raw numeric on its
    # own). Raw ints are dropped from the output table in favor of this.
    reg = pd.to_datetime(df["registration_init_time"], format="%Y%m%d")
    exp = pd.to_datetime(df["expiration_date"], format="%Y%m%d")
    out["membership_duration_days"] = (exp - reg).dt.days

    # --- Low-cardinality categoricals: explicit missing category, then
    # one-hot. Cardinalities (8/19/12/21/2/5/10) are all one-hot-friendly
    # per 01-data.md.
    for col in LOW_CARD_CATS:
        filled = df[col].astype("object").fillna("missing").astype(str)
        dummies = pd.get_dummies(filled, prefix=col, dtype=int)
        out = pd.concat([out, dummies], axis=1)

    # --- Combined listening-context interaction feature ---
    # monkey-mode's Suggested Next Steps named this explicitly: "richer
    # encodings of listening context (e.g. combined tab+screen+type
    # interaction terms)," since source_system_tab/source_screen_name/
    # source_type one-hot levels made up 8 of its top 15 feature
    # importances on their own. Frequency-encoded (not one-hot) since the
    # combo space is large (up to 8*19*12) even though few combos are
    # actually realized.
    # fillna before astype(str): found via a real bug that .astype(str) on
    # this pandas version does NOT stringify NaN to "nan" - it stays NaN,
    # which silently propagated into ~5.6% of source_context_freq (matching
    # source_screen_name's null rate exactly). fillna first, consistent
    # with how every other categorical column here handles missingness.
    context = (
        df["source_system_tab"].fillna("missing").astype(str) + "|"
        + df["source_screen_name"].fillna("missing").astype(str) + "|"
        + df["source_type"].fillna("missing").astype(str)
    )
    context_freq = context.map(context.value_counts(normalize=True))
    out["source_context_freq"] = context_freq
    pd.DataFrame({"source_context": context.unique()}).assign(
        freq=lambda d: d["source_context"].map(context.value_counts(normalize=True))
    ).to_csv(f"{OUT_DIR}/context_freq.csv", index=False)

    # --- artist_name: two distinct signals, kept separately ---
    # Popularity (frequency encoding) and stickiness (the smoothed
    # repeat-rate built above) measure different things - a very popular
    # artist isn't necessarily one people replay, and vice versa. Both are
    # cheap (one groupby each), so both are kept rather than picking one.
    artist_filled = df["artist_name"].fillna("missing")
    artist_freq = artist_filled.map(artist_filled.value_counts(normalize=True))
    out["artist_name_freq"] = artist_freq
    pd.DataFrame({"artist_name": artist_filled.unique()}).assign(
        freq=lambda d: d["artist_name"].map(artist_filled.value_counts(normalize=True))
    ).to_csv(f"{OUT_DIR}/artist_freq.csv", index=False)

    # --- genre_ids: one-hot top-15 primary genres + "other" ---
    # First pass frequency-encoded the primary genre id. On review that's a
    # bad idea: frequency encoding collapses distinct genres that happen to
    # have similar popularity into the same feature value, discarding
    # exactly the genre-identity signal a music recommender should care
    # about (two equally-common but musically unrelated genres become
    # indistinguishable to the model). Fixed with one-hot over the top 15
    # most frequent primary genres (covers the large majority of rows,
    # per 01-data.md's cardinality-370 profile) plus a bucket for
    # everything else - preserves identity for the common cases without
    # the dimensionality blowup a full 370-column one-hot would cause.
    genre_primary = df["genre_ids"].astype(str).str.split("|").str[0]
    top_genres = genre_primary.value_counts().head(15).index.tolist()
    genre_primary_top = genre_primary.where(genre_primary.isin(top_genres), "other")
    genre_dummies = pd.get_dummies(genre_primary_top, prefix="genre_primary", dtype=int)
    out = pd.concat([out, genre_dummies], axis=1)
    pd.DataFrame({"genre_primary": top_genres}).to_csv(
        f"{OUT_DIR}/genre_primary_top.csv", index=False
    )

    # --- Dropped entirely: isrc_country, name, composer, lyricist ---
    # isrc_country (a 2-char country-code proxy parsed from isrc, used in
    # monkey-mode's baseline at low importance): dropped on review - this
    # project already has `language` (10 categories, one-hot) capturing
    # very similar geographic/linguistic signal, so isrc_country is mostly
    # redundant, and it needs its own lookup table for test-time joins for
    # marginal expected value. Not worth the added complexity.
    # name: free-text song title. Considered cheap text-signal features
    # (length, word count) newly documented in this skill instead of a
    # full drop, but declined - title length is a weak, redundant proxy
    # for exactly what `song_length_log` already measures more directly
    # (the long-form-content outliers found while reviewing the dashboard
    # were DJ mixes/continuous mixes with long titles AND long durations;
    # duration is the more precise, already-captured signal).
    # composer/lyricist: free-text, high null rate (22.7% / 43.0% per
    # 01-data.md) and high cardinality - monkey-mode's baseline didn't use
    # them either and they contributed nothing to its top-15 importances.

    out.to_csv(f"{OUT_DIR}/kkbox_train_features.csv", index=False)
    print(f"rows={len(out)} cols={out.shape[1]}")
    print(f"output columns: {list(out.columns)}")


if __name__ == "__main__":
    main()
