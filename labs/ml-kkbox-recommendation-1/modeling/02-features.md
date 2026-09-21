# 02 - Features (Quick POC)

Input table: `modeling/datasets/kkbox_train.csv` (`01-data.json` ->
`dataset.train`). `dataset.test` was not opened.

Grounding: `design/high-level.md`'s ML framing (unit of prediction: one
(user, song) row), `modeling/01-data.md`'s profile and risk flags, and
`monkey-mode/report.md`'s baseline (AUC 0.6727) - its feature-importance
and Suggested Next Steps sections drove several choices below directly,
called out inline.

## Output table

`modeling/datasets/kkbox_train_features.csv` (480,000 rows, 112 columns),
written by `modeling/build_features.py`. Six small lookup tables are also
written for reuse at evaluation time - see "Applying to the test split"
below:

- `modeling/datasets/msno_repeat_rate.csv`
- `modeling/datasets/song_repeat_rate.csv`
- `modeling/datasets/artist_repeat_rate.csv`
- `modeling/datasets/artist_freq.csv`
- `modeling/datasets/genre_primary_top.csv`
- `modeling/datasets/context_freq.csv`

This is the second pass over this file's feature set. Re-run per
`/ml-modeling-features ... drop bad ideas from the insights if necessary`,
`ml-modeling-features/SKILL.md`'s newly-added sections (aggregation
smoothing, embeddings note), and a critical re-read of `monkey-mode/
report.md`. Two ideas from the first pass didn't survive review - see
"What was tried and dropped" - and the leave-one-out rates gained
smoothing. Column count grew 96 -> 112 mainly from replacing one
frequency-encoded genre column with 16 one-hot genre columns (top 15 +
other), a deliberate tradeoff explained below.

## What was tried and kept

**Per-user, per-song, and per-artist historical repeat-listen rate
(smoothed, leave-one-out).** `monkey-mode/report.md`'s Suggested Next
Steps named this explicitly: "aggregates were out of scope for this fast
baseline but are a natural next feature group to try." Built as
`msno_repeat_rate_loo` + `msno_count`, `song_repeat_rate_loo` +
`song_count`, and (added on this review pass) `artist_repeat_rate_loo` +
`artist_count`. Leave-one-out (each row's own `target` excluded from its
own group's rate) because every row is one (user, song) pair - a plain
group mean would encode the row's own label directly into its own
feature, which is direct target leakage, not a subtler timing leak.

**Revised on review**: the first pass used a raw LOO rate with a single
fallback (`fillna(global_mean)`) for count==1 groups only - a bad idea
past count==1 too. A count==2 group's LOO rate is either exactly 0% or
100% from a single other observation, which is noise, not signal, and
the raw formula treated it as confidently as a count-2,000 group.
Replaced with count-weighted shrinkage toward the global mean
(`smoothed = (others_sum + k*global_mean) / (others_count + k)`, k=10 -
using `ml-modeling-features/SKILL.md`'s newly-documented smoothed target
encoding, generalized to the leave-one-out case): a group needs roughly
10 observations before its own rate is trusted much over the global
average, and the formula degrades to exactly `global_mean` at
count-1==0, so the separate count==1 special case is gone too - one
formula covers every group size correctly. `*_count` is kept alongside
each rate as an exposure signal even with smoothing, since a model still
benefits from knowing how much weight backs a given smoothed value.

**`artist_repeat_rate_loo` is new this pass**, alongside the
already-kept `artist_name_freq` (see below) - popularity and stickiness
are different signals (a very popular artist isn't necessarily one
people replay, and vice versa), so both are kept rather than picking
one; the smoothing above makes the rate side safe to add for
low-count artists too.

**Combined listening-context feature (`source_context_freq`).**
`monkey-mode/report.md`'s feature-importance table found the top 8 of
its top 15 importances were all one-hot levels of `source_system_tab`,
`source_screen_name`, and `source_type` individually, and its Suggested
Next Steps named "richer encodings of listening context (e.g. combined
tab+screen+type interaction terms)" as the first thing to try before
investing further in demographics. Built as a frequency encoding of the
three columns concatenated (`tab|screen|type`) - frequency, not one-hot,
since the combination space (up to 8x19x12) is large even though few
combinations are actually realized in the data.

**Low-cardinality categorical one-hot**: `source_system_tab` (8),
`source_screen_name` (19), `source_type` (12), `city` (21), `gender`
(2), `registered_via` (5), `language` (10) - all one-hot-friendly per
`01-data.md`. Nulls get an explicit `missing` category first (visible in
`source_system_tab_missing`, `gender_missing`, etc.) rather than being
silently dropped or imputed into an arbitrary existing category.

`gender` specifically was kept despite `monkey-mode/report.md` flagging
it as "null in 40% of rows and ranked low in importance... a reasonable
candidate to deprioritize or drop": one-hot encoding it costs almost
nothing (2 extra columns + a missing flag), and a tree-based model
naturally down-weights a low-signal column rather than being hurt by
its presence - so there's no reason to drop it preemptively. Flagged
here as a candidate `ml-modeling-train`/`-multiagent` should re-check
with the actual trained model's feature importances, and drop then if
monkey-mode's finding holds.

**`bd` (member age) + `bd_missing` flag.** `01-data.md` already masked
implausible values (<=0 or >100) to null in the data step; this step
adds `bd_missing` as an explicit indicator, on the same reasoning as the
other missing-category treatment above - "was invalid" is itself
potentially informative, and shouldn't be silently merged into an
imputed value. Actual imputation/scaling is left to the training step's
pipeline (matching `monkey-mode/report.md`'s own division of labor:
engineer/flag here, impute+scale inside the model pipeline), so this
feature table stays imputation-strategy-agnostic.

**`song_length_log`.** `log1p(song_length)`, justified directly by
`01-data.md`'s flagged skew of 17.32 and its own note "a log transform
is worth considering later."

**`membership_duration_days`.** `registration_init_time` and
`expiration_date` are `YYYYMMDD`-encoded integers - `01-data.md` flagged
neither as meaningful as a raw numeric on its own ("their mean/median/std
are arithmetic on the encoding, not calendar time"). Parsed to dates and
subtracted into one interpretable duration feature; the two raw
int-encoded columns are dropped from the output table in favor of it.

**`artist_name_freq`** (15,239 distinct, frequency-encoded): this
skill's own guidance - "target or frequency encoding for high-cardinality
columns" - over one-hot, which would blow up dimensionality. Kept
alongside the new `artist_repeat_rate_loo` above (see reasoning there).

**`genre_primary` one-hot, top 15 + other** (revised on review -
see "What was tried and dropped" for what this replaced). `genre_ids`
(370 distinct, sometimes multi-valued e.g. `"465|444"`) - only the first
id is kept, discarding secondary genres for this POC. The top 15 most
frequent primary genres each get their own one-hot column; everything
else collapses into `genre_primary_other`. This covers the large
majority of rows as named categories while still bounding dimensionality
for the long tail of the other ~355 rarer genres.

## What was tried and dropped

- **`genre_primary_freq`** (frequency encoding of the primary genre id -
  what the first pass used): dropped on review, not just left as-is.
  Frequency encoding collapses distinct genres that happen to have
  similar popularity into the *same* feature value - two musically
  unrelated genres with matching row counts become indistinguishable to
  the model, discarding exactly the genre-identity signal a music
  recommender should care about. Replaced with one-hot top-15 + other
  (above), which costs 15 extra columns but preserves identity for the
  genres that matter most.
- **`isrc_country_freq`** (a 2-character country-code proxy parsed from
  `isrc`, used in `monkey-mode/report.md`'s baseline at low importance):
  dropped on review. This project already has `language` (10 categories,
  one-hot) capturing very similar geographic/linguistic signal, so this
  column was mostly redundant, and it needed its own lookup table for
  test-time joins for marginal expected value - not worth the added
  complexity for a column monkey-mode's own baseline already found
  unimportant.
- **Cheap text-signal features for `name`** (song title length/word
  count - the efficient no-embeddings alternative
  `ml-modeling-features/SKILL.md` now documents): considered on this
  review pass, declined. Title length is a weak, redundant proxy for
  exactly what `song_length_log` already measures more directly - the
  long-form-content outliers found while reviewing the EDA dashboard
  (DJ mixes, continuous mixes) have both unusually long titles *and*
  unusually long durations, and duration is the more precise signal
  already captured.
- **`name`** (song title, free text): no NLP planned for this POC,
  and the cheap-text-signal alternative was also declined above -
  dropped entirely.
- **`composer`, `lyricist`** (free text): 22.7% / 43.0% null per
  `01-data.md`, high cardinality, and absent from `monkey-mode/
  report.md`'s baseline entirely - dropped rather than encoded, since
  neither the profile nor the baseline gave any signal they'd help.
- **`msno`, `song_id`** raw values: never used directly as features (no
  generalization value at that cardinality) - only as join keys for the
  leave-one-out aggregates above.
- **Multi-valued `genre_ids`** (secondary genres beyond the first):
  still dropped for this POC rather than exploded into a multi-hot
  representation - the primary genre alone (now one-hot, not frequency)
  was judged a reasonable first cut; multi-hot genre is a candidate for
  a later iteration.

## Selection check

`../ml-modeling/scripts/feature_selector.py --file modeling/datasets/
kkbox_train_features.csv --target target --top 20` re-run against the
revised output table (112 columns, ~3 minutes).

Top 20 by composite score, condensed - full output is reproducible by
re-running the command above:

1. `source_screen_name_Local playlist more` (0.4448)
2. `source_system_tab_my library` (0.4431)
3. `source_type_local-library` (0.4163)
4. `song_count` (0.409) - a leave-one-out exposure count, not the rate
   itself
5. `source_type_radio` (0.4082)
6. `source_screen_name_Radio` (0.4081)
7. `source_system_tab_radio` (0.4073)
8. `source_type_local-playlist` (0.3988)
9. `source_system_tab_discover` (0.3919)
10. **`source_context_freq`** (0.3854) - the combined-context feature
    built specifically because of monkey-mode's Suggested Next Steps
11. `source_type_online-playlist` (0.3847)
12. `source_screen_name_Online playlist more` (0.3799)
13. `source_screen_name_Others profile more` (0.3737)
14. `source_system_tab_listen with` (0.3726)
15. `source_type_listen-with` (0.3724)
16. `source_type_album` (0.3709)
17. `source_screen_name_Album more` (0.37)
18. **`artist_count`** (0.3685) - new this pass, the artist-side exposure
    count from `artist_repeat_rate_loo`
19. **`artist_name_freq`** (0.3685) - the frequency-encoded high-cardinality feature
20. `source_system_tab_search` (0.3682)

Same story as the first pass, reconfirmed: listening context still
dominates the top of the list, and `source_context_freq` and the two
leave-one-out exposure counts (`song_count`, and now `artist_count`)
land inside the top 20. Adding `artist_repeat_rate_loo` this pass
surfaced its exposure count as a new top-20 entry, right alongside the
already-validated `artist_name_freq`.

Not in the top 20, same as the first pass: `msno_repeat_rate_loo`,
`song_repeat_rate_loo`, `artist_repeat_rate_loo` themselves (the smoothed
rates, not their counts), and none of the 16 `genre_primary_*` one-hot
columns. This tool's composite score weights variance/null-completeness/
correlation in a way that favors binary one-hot dummies over a
continuous rate or a column split across many rare categories - not
strong evidence to drop any of these, since it's a correlation/variance
heuristic, not a trained model's importance. All kept; worth rechecking
against `ml-modeling-train`'s actual model-based feature importances
once step 3 runs - genre and the three repeat-rate columns are the ones
most worth re-examining then, alongside `gender` (flagged above).

## Applying to the test split

`ml-modeling-train`/`ml-modeling-evaluate` must build the equivalent
feature table for `modeling/datasets/kkbox_test.csv` before scoring -
this file was never opened here by design, so that work is explicitly
handed off:

- `song_length_log`, `membership_duration_days`, `bd_missing`, and the
  low-cardinality one-hot columns are deterministic transforms of
  columns already present in `kkbox_test.csv` - recompute them directly
  with the same logic as `build_features.py`, no lookup needed. For
  one-hot, align test's dummy columns to train's column set (a category
  unseen in train produces an all-zero row; a train category absent
  from test's realized values still needs its all-zero column present).
- `msno_repeat_rate_loo`, `song_repeat_rate_loo`, `artist_repeat_rate_loo`,
  and `artist_name_freq` must be **left-joined** from their lookup CSVs
  (train-derived, no leave-one-out for test rows - a test row was never
  part of the aggregate it's being joined against, so no leakage). The
  three repeat-rate lookups already store the smoothed value (see "What
  was tried and kept"), so the join is a straight left-join, no
  recomputation. A key present in test but absent from a lookup table (a
  user/song/artist never seen in train) needs a fallback: the global
  mean for the three repeat-rate lookups (the smoothing formula's
  natural fallback), or 0 for `artist_freq` (meaning "unseen," itself
  informative).
- `genre_primary` one-hot needs `modeling/datasets/genre_primary_top.csv`
  (the 15 genre ids that became their own column): recompute the primary
  genre id on test the same way, map anything not in that list to
  `"other"`, then one-hot with the same 16 columns as train (a genre
  id in train's top 15 that never appears in test still needs its
  all-zero column present).
- `source_context_freq` needs the same treatment: recompute the
  `tab|screen|type` string on test, then left-join through
  `modeling/datasets/context_freq.csv`.

## Looking ahead: model class

Not this step's decision (that's `ml-modeling-train`'s), but worth
recording the signal this step's encoding choices were made against:
`monkey-mode/report.md` already cleared the 0.65 AUC bar with a single,
untuned `RandomForestClassifier` and suggested "a gradient-boosted tree
model (e.g. LightGBM/XGBoost) is a sound V1 model-class bet." The
encodings above (one-hot + frequency, no target encoding, no
interaction terms beyond `source_context_freq`) are tree-model-friendly
but not tree-model-*specific* - they'd also work for a linear baseline
- so this step doesn't lock `ml-modeling-train` into a tree model,
it just doesn't fight one either.

## Change log

- 2026-09-21: initial feature engineering pass for the Quick POC.
- 2026-09-21: added a note on `gender` cross-referencing
  `monkey-mode/report.md`'s finding that it's low-null-value/low-
  importance - a gap noticed while re-reading that report for
  insights not yet reflected anywhere in this project's docs. No
  feature-set change, documentation only.
- 2026-09-21: critical review pass against `ml-modeling-features/
  SKILL.md`'s newly-added sections and a re-read of `monkey-mode/
  report.md`, per explicit instruction to drop bad ideas if
  necessary. Dropped `isrc_country_freq` (redundant with `language`).
  Replaced `genre_primary_freq` with one-hot top-15 + other (frequency
  encoding was collapsing distinct genres of similar popularity into
  the same value). Applied count-weighted smoothing (k=10) to the
  `msno`/`song` leave-one-out rates, replacing the old single-fallback
  raw LOO formula. Added `artist_repeat_rate_loo` (smoothed LOO)
  alongside the existing `artist_name_freq`. Considered and declined
  cheap text-signal features for `name` (redundant with
  `song_length_log`). Column count: 96 -> 112. Datasets and lookup
  tables regenerated; obsolete lookup files removed.
- 2026-09-21: fixed two real bugs in `build_features.py`, found while
  diagnosing a CV-leakage issue during `ml-modeling-multiagent`
  training (see `03-train.md`). (1) `.astype(str)` on this pandas
  version does not stringify NaN to the string `"nan"` - it silently
  stays NaN - which was propagating through the `source_context`
  concatenation into ~5.6% NaN in `source_context_freq` (exactly
  `source_screen_name`'s null rate). Fixed with `.fillna("missing")`
  before `.astype(str)` for all three source columns, consistent with
  how every other categorical column here handles missingness
  explicitly. (2) 17 rows have NaN `artist_name` (a `songs.csv` join
  gap - the same 17 rows also have NaN `song_length`, confirmed not a
  separate issue), and pandas `groupby` silently drops NaN-keyed
  groups by default, so those rows got NaN in `artist_name_freq`,
  `artist_repeat_rate_loo`, and `artist_count` instead of an explicit
  "missing" bucket. Fixed by filling `artist_name`'s NaN with
  `"missing"` before grouping. `song_length_log`'s NaN for those same
  17 rows is unaffected and still legitimate (real missing data from
  the join gap, not a bug) - still needs imputation downstream.
  Re-ran `build_features.py`; only `bd` and `song_length_log` have any
  NaN in the output table now, both expected and already documented.
