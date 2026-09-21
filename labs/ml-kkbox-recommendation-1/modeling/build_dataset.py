"""Build the labeled table for the KKBOX repeat-listen POC.

train.csv already carries the label (`target`), computed by KKBOX from
underlying listening logs not exposed at row level in this dataset (no
per-row timestamp exists for a (msno, song_id) pair - see 01-data.md). A
random, stratified split is therefore used instead of a time-based cutoff.

Sampling: the full train.csv is ~7.4M rows; we sample 600,000 rows
(stratified by target) to keep this POC's iteration loop fast, matching
the sample size already validated in monkey-mode/report.md.

song_length is converted from milliseconds (as stored in songs.csv) to
seconds for readability - see 01-data.md's Change log.
"""

import pandas as pd
import numpy as np

DATA_DIR = "/Users/alex/dev/sandbox/data/kkbox/extracted"
OUT_DIR = "modeling/datasets"
SAMPLE_SIZE = 600_000
TEST_SHARE = 0.2
SEED = 42

def main():
    train = pd.read_csv(f"{DATA_DIR}/train.csv")

    sampled, _ = train_test_stratified_sample(train, SAMPLE_SIZE, SEED)

    members = pd.read_csv(f"{DATA_DIR}/members.csv")
    songs = pd.read_csv(f"{DATA_DIR}/songs.csv")
    song_extra = pd.read_csv(f"{DATA_DIR}/song_extra_info.csv")
    song_extra = song_extra.drop_duplicates(subset="song_id", keep="first")
    songs = songs.drop_duplicates(subset="song_id", keep="first")

    joined = (
        sampled
        .merge(members, on="msno", how="left")
        .merge(songs, on="song_id", how="left")
        .merge(song_extra, on="song_id", how="left")
    )
    joined = joined.reset_index(drop=True)
    joined.insert(0, "row_id", joined.index)

    # songs.csv stores song_length in milliseconds; convert to seconds for
    # a human-readable unit throughout this project's tables/profile/dashboard.
    joined["song_length"] = joined["song_length"] / 1000

    # bd (self-reported age) has known-invalid values (<=0 or >100) - a data
    # entry artifact, not a real extreme value like a long song. Mask to NaN
    # rather than dropping rows, so downstream steps treat it as missing.
    bd_invalid = (joined["bd"] <= 0) | (joined["bd"] > 100)
    joined.loc[bd_invalid, "bd"] = np.nan

    pos_rate = joined["target"].mean()
    assert 0.05 < pos_rate < 0.95, (
        f"Degenerate positive rate ({pos_rate:.4f}) - check for a leak or a "
        "drifted rule before proceeding."
    )

    rng = np.random.RandomState(SEED)
    is_test = np.zeros(len(joined), dtype=bool)
    for label in (0, 1):
        idx = joined.index[joined["target"] == label].to_numpy().copy()
        rng.shuffle(idx)
        n_test = int(len(idx) * TEST_SHARE)
        is_test[idx[:n_test]] = True

    train_df = joined.loc[~is_test].reset_index(drop=True)
    test_df = joined.loc[is_test].reset_index(drop=True)

    import os
    os.makedirs(OUT_DIR, exist_ok=True)
    train_df.to_csv(f"{OUT_DIR}/kkbox_train.csv", index=False)
    test_df.to_csv(f"{OUT_DIR}/kkbox_test.csv", index=False)

    print(f"sampled_rows={len(joined)} pos_rate={pos_rate:.4f}")
    print(f"train_rows={len(train_df)} test_rows={len(test_df)}")
    print(f"train_pos_rate={train_df['target'].mean():.4f} "
          f"test_pos_rate={test_df['target'].mean():.4f}")


def train_test_stratified_sample(df, n, seed):
    rng = np.random.RandomState(seed)
    pos = df.index[df["target"] == 1].to_numpy().copy()
    neg = df.index[df["target"] == 0].to_numpy().copy()
    rng.shuffle(pos)
    rng.shuffle(neg)
    pos_share = len(pos) / len(df)
    n_pos = int(round(n * pos_share))
    n_neg = n - n_pos
    idx = np.concatenate([pos[:n_pos], neg[:n_neg]])
    rng.shuffle(idx)
    return df.loc[idx].reset_index(drop=True), idx


if __name__ == "__main__":
    main()
