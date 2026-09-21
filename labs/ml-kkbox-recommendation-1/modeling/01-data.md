# 01 - Data (Quick POC)

## Dataset

`train.csv` already carries the label (`target`) precomputed by KKBOX,
so this is the "flat labeled table" case, not the raw-logs case - no
`build_dataset.py` label-construction logic was needed, only a join
and a split.

Source tables (all named in `design/high-level.md`'s Architecture,
all present, no drift): `train.csv`, `members.csv`, `songs.csv`, and
`song_extra_info.csv`, unzipped from
`data/kkbox/kkbox-music-recommendation-challenge.zip` into
`data/kkbox/extracted/`. The competition's `test.csv` has no label
column (it is the Kaggle submission set) and is not used for this
project's evaluation.

`modeling/build_dataset.py`:

1. Loads the full `train.csv` (7,377,419 rows) and takes a
   class-stratified sample of 600,000 rows (**~8.1% of the full
   `train.csv`**), seed 42 - matching the sample size already
   validated end-to-end in `monkey-mode/report.md` (AUC 0.6727 on a
   similar sample), so this project's split builds on a known-workable
   scale rather than guessing at one. This project never trains on the
   full 7.4M-row table - worth keeping in mind alongside the missing
   `user_logs.csv` table (below) when judging how this compares to
   anything trained on the complete dataset, including the real Kaggle
   leaderboard (see `04-evaluate.md`, "Not comparable to the public
   leaderboard").
2. Left-joins the sample with `members.csv` (on `msno`) and
   `songs.csv` + `song_extra_info.csv` (on `song_id`, each deduped on
   `song_id` first - `song_extra_info.csv` has 36 more rows than
   `songs.csv`'s distinct `song_id` count).
3. Adds a synthetic `row_id` (there is no natural single-column id in
   `train.csv`), converts `song_length` from milliseconds (as stored
   in `songs.csv`) to seconds for readability, and masks `bd`
   (member age) values <= 0 or > 100 to null - a known KKBOX data
   artifact, not a real extreme value, so it is corrected here rather
   than left to distort every downstream stat and feature.
4. Splits into `modeling/datasets/kkbox_train.csv` (480,000 rows) and
   `modeling/datasets/kkbox_test.csv` (120,000 rows), 80/20,
   stratified by `target`, seed 42.
5. Asserts the positive rate isn't degenerate before writing - it
   came out to 50.35%, so this is not a leak/drift check that fired.

**Split type: random, not time-based.** `design/high-level.md`'s ML
framing calls this a time-windowed label (repeat listen within a
1-month horizon), which per this skill's default would call for a
cutoff-based split. That default assumes row-level event timestamps
exist to cut on. They don't: this WSDM release has no `user_logs.csv`
(only `train.csv`, `test.csv`, `members.csv`, `songs.csv`,
`song_extra_info.csv`, `sample_submission.csv` are in the zip), and
`train.csv` itself carries no per-row date - `target` is a value
KKBOX precomputed from logs this dataset doesn't expose. `bd`
(age), `registration_init_time`, and `expiration_date` are
member-level, not event-level, so they can't stand in for a row date
either. A random, class-stratified split with a fixed seed is
therefore the correct call here, not a shortcut - there is no
timestamp in hand to cut on. This is worth flagging back to
`design/high-level.md` if the project ever adds `user_logs.csv`
(not part of this release) as a feature source; noted, not applied,
since it doesn't change this step's split decision today.

`dataset` block written to `01-data.json`. `built_by`:
`modeling/build_dataset.py`.

## Profile (train split only, 480,000 rows x 21 columns, 178.7 MB)

**Nulls**: three columns clear the 20% risk threshold - `bd` (39.97%,
entirely from the outlier-masking in `build_dataset.py`, not source
data gaps), `gender` (40.2%), and `lyricist` (43.0%); `composer` is
close at 22.7%. All need explicit missing handling in feature
engineering - `bd` and `composer`/`lyricist`/`gender` shouldn't be
silently imputed as if the value were simply absent, since `bd`'s
nulls specifically mean "was invalid," not "unknown." Everything else
is under 6% null (`source_screen_name` highest among the rest, at
5.6%).

**Target**: `target` is close to balanced - 50.35% positive
(repeat listen), 49.65% negative. Class-imbalance handling is not a
priority for this model.

**Numeric distributions** (min / max / mean / median / std / skew -
median added alongside mean so a skewed column's "typical" value
isn't read off the mean alone):

`bd` (member age), after masking invalid values to null: min 2, max
95, mean 28.72, **median 27**, std 8.63, skew 1.3 - a mild, plausible
right skew for an age distribution, once the corrupted rows (`bd`
<= 0 or > 100, a known KKBOX data-quality issue in the self-reported
age field) are excluded. Before masking this column's skew was 22.26
(min -43, max 1030) - the outliers, not real age variation, were
driving that number.

`song_length` (seconds) ranges from 1.4s to 7,575.8s (~2 hours), mean
245.0s, **median 241.7s** (mean and median are close - this column's
skew of 17.32 comes from a long tail of long tracks, not a few
corrupt values, so it was left unmasked) - plausible for a catalog
that includes long-form audio, but a log transform is worth
considering later.

`registration_init_time` (mean 20128112.22, median 20131022.0) and
`expiration_date` (mean 20171575.38, median 20170926.0) are stored as
`YYYYMMDD` integers (e.g. 20110820), not proper dates, so their
mean/median/std are arithmetic on the encoding, not calendar time -
fine for ordering/comparison, but any date-arithmetic feature in the
next step needs to parse them first. `expiration_date`'s skew (-3.45)
reflects most accounts clustering near a common expiration date with
a long tail of much earlier ones, not a data error.

**Categorical distributions**:

`source_system_tab` (8), `source_screen_name` (19), `source_type`
(12), `city` (21), `registered_via` (5), and `language` (10) are all
low-cardinality and one-hot-friendly. `genre_ids` (370 distinct
values, some multi-valued e.g. "465|444") and `artist_name` (15,239
distinct) are high-cardinality and will need a different treatment
(frequency encoding or top-N + "other") in feature engineering rather
than a naive one-hot.

**Quality flags** (also recorded in `01-data.json`):

- 40.0% of rows had an implausible `bd` (member age) and were masked
  to null in `build_dataset.py` (see Dataset section above).
- `bd`, `gender`, `composer`, `lyricist` all exceed or approach the
  20% null-rate risk threshold.
- No table named in `design/high-level.md`'s Architecture was missing
  or renamed - no drift to reconcile.

## Dashboard

`dashboard/eda.ipynb` built with real executed cells (shape, nulls,
target balance, numeric/categorical distributions - the same facts
as above). `dashboard/app.py` copied from the shared template
(`assets/dashboard_app.py`) and launched as a background Streamlit
process. See the session's report for the live URL and port.

## Change log

- 2026-09-20: initial data step for the Quick POC.
- 2026-09-21: `song_length` converted from milliseconds to seconds in
  `build_dataset.py` for readability; re-ran the build and profiling,
  updating the stats above and in `01-data.json` (min/max/mean/std
  scaled by 1000, skew unaffected). Datasets under
  `modeling/datasets/` were regenerated with the same seed/split, so
  row membership is unchanged.
- 2026-09-21: masked `bd` (member age) values <= 0 or > 100 to null
  in `build_dataset.py` (previously left as-is, flagged only as a
  risk); added `median` alongside `mean` to every numeric
  distribution. Re-ran the build and profiling - `bd`'s skew dropped
  from 22.26 to 1.3 once the corrupted values were excluded, and its
  null rate rose from 0% to 39.97% to reflect the masking. Datasets
  under `modeling/datasets/` were regenerated with the same
  seed/split. Dashboard rebuilt (EDA notebook re-executed, Streamlit
  process relaunched) to reflect all of the above.
- 2026-09-21: re-ran this step against `ml-modeling-data`'s newly
  formalized Clean section (impossible-vs-unusual test). Checked for
  additional impossible values beyond the `bd` masking already done:
  `expiration_date` < `registration_init_time` (0 rows),
  out-of-range `city`/`registered_via` codes (none), non-positive
  `song_length` (0 rows), duplicate `(msno, song_id)` pairs (0) - none
  found, so no further cleaning was needed. Also fixed a transcription
  bug found during the re-run: `01-data.json`'s `artist_name` top
  value "田饆眜 (Hebe)" was mangled (should be "田馥甄 (Hebe)", Hebe
  Tien) - a typo from hand-typing the JSON earlier, not a data issue.
  Datasets regenerated (identical output, confirmed byte-for-byte
  equivalent stats). Dashboard rebuilt and relaunched.
- 2026-09-21: added the explicit ~8.1% sample-size percentage to the
  Dataset section (the raw counts were always there, but the
  percentage itself wasn't stated) - the user asked whether the fact
  that this project trains on a sample, not the full dataset, was
  documented; it wasn't, clearly enough, until now.
