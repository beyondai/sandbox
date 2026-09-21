---
name: ml-modeling-features
description: >-
  Use to engineer and select features for an ML model — numerical transforms,
  categorical encoding, leave-one-out aggregation features, interaction/cross
  features, time-based/cyclical features, importance-based selection. Step 2
  of the ml-modeling-* chain (data → features → train → evaluate). Trigger on
  "engineer features for this," "encode these columns," or continuing
  modeling work in an existing ml-<topic>-<n>/ project.
---

# Engineer Features

Reads `<project-folder>/design/high-level.md`'s ML framing (population, unit of
prediction — what one row is) and `modeling/01-data.md` (the profile and its
risk flags). The feature list is this step's decision, recorded in
`02-features.md`; there is no upstream list to copy. Writes
`<project-folder>/modeling/02-features.md`. Project folder and output format: see `../ml-modeling/SKILL.md`,
"Which project folder" and "Output docs". First, run the "Design docs
changed?" check from `../ml-modeling/SKILL.md`.

Input table: `01-data.json` -> `dataset.train`. Never open `dataset.test`
here. If you write a transformed table, save it under `modeling/datasets/`
and record its path in `02-features.md` under "Output table" so train picks
it up.

Mode: Regular proposes transforms from the profile and the framing, then checks
importance before finalizing. Quick POC picks the most obviously useful
transforms and moves on — see `ml-modeling` router for the keyword rule.

## Numerical transforms

```python
def engineer_numerical(df, col):
    return pd.DataFrame({
        f'{col}_log':     np.log1p(df[col]),
        f'{col}_sqrt':    np.sqrt(df[col].clip(lower=0)),
        f'{col}_squared': df[col] ** 2,
        f'{col}_binned':  pd.cut(df[col], bins=5, labels=False),
    })
```

**Missing-value indicator flags**: for any numeric column with a
non-trivial null rate, add a binary `{col}_missing` column alongside it -
"was this invalid/absent" stays visible as a signal even after imputation
happens later in the training pipeline.

**Prefer quantile bins for skewed columns**: swap `pd.cut` (fixed-width)
for `pd.qcut` (quantile-based) when the profile flags a column as skewed -
fixed-width bins on a skewed column put almost every row into one bin.

## Categorical encoding

One-hot for low cardinality; target or frequency encoding for high-cardinality
columns (e.g. `user_id`) — one-hot there would blow up dimensionality.

**Smoothed/regularized target encoding**: shrink a category's target mean
toward the global mean, weighted by that category's row count -
`smoothed = (count * cat_mean + k * global_mean) / (count + k)` - so a
rarely-seen category isn't treated as confidently as a common one. Cheap
(one groupby), meaningfully more effective than naive mean encoding.

## Aggregation features (leave-one-out safe)

Per-entity historical stats - mean/count/std of the target, or of another
numeric column, grouped by whatever categorical id represents the framing's
population (a user, item, session, or similar entity). Often the highest-value
feature group available and cheap to compute (one groupby), but only safe
under one condition:

**Leave-one-out is mandatory when the aggregate includes the row's own
label.** Exclude the row's own value from its own group's statistic:

```python
count = df.groupby(entity_col)[target_col].transform('count')
total = df.groupby(entity_col)[target_col].transform('sum')
loo_rate = (total - df[target_col]) / (count - 1)
loo_rate = loo_rate.fillna(df[target_col].mean())  # count == 1 groups
```

Skipping this is direct target leakage - the label leaking into its own
feature, not a subtler timing leak. Always keep the count/exposure alongside
the rate: a rate from 2 rows and a rate from 2,000 aren't equally
trustworthy, and a model benefits from knowing which.

Persist a small lookup table (`<entity id> -> rate, count`) so
`ml-modeling-train`/`-evaluate` can **left-join** (not leave-one-out) the
same stat onto the held-out test split - test rows were never part of the
training aggregate, so a plain join is leakage-free there.

**Warning, not a footnote: this column is not automatically safe under
k-fold CV.** Row-level leave-one-out only excludes a row's own label from
its own group statistic - it does not exclude every other row from the
same CV validation fold. If this column is computed once, globally, before
a k-fold split (rather than re-derived per fold from that fold's train
portion only), rows in a validation fold still leak into each other's
aggregate features whenever they share an entity. This is not a small,
uniform effect: a gradient-boosted/iterative model can exploit that
fold-crossing leak far more aggressively than a bagged or linear model can,
so it can flip which candidate looks like the winner in exactly the
scenario `ml-modeling-train`/`-multiagent` compare candidates for.
Recompute this column per fold (same leave-one-out-within-the-fold,
smoothed-mean-onto-the-validation-fold pattern as the test-split left-join
above, just run once per fold) before trusting a CV ranking that includes
it - or explicitly flag the ranking as provisional pending the real
held-out evaluation in `ml-modeling-evaluate` if recomputing per fold isn't
done.

## Embeddings (not used in Quick POC)

Not used by default: training your own embeddings doesn't fit a POC's time
budget, and a pretrained one can't be fine-tuned to the task in that time
either, so it would stay a generic, unadapted representation rather than one
that's learned anything about this problem. Self-hosting a pretrained
embedding model is a future possibility, on hold for now - not effective on
a personal laptop (resource-constrained for local model inference at any
real scale). Default stays frequency/target encoding (above) for
categoricals and IDs, regardless of mode - see "Cheap text signals" below
for the efficient fallback on a free-text column.

## Interaction / cross features

Concatenate two or three categorical columns into one, or take a
ratio/product of two related numeric columns - only when profile evidence or
the framing's domain reasoning suggests a joint effect isn't captured by
either column alone. Not a combinatorial auto-generate-everything pass:
same "justified, not applied by default" rule as every other transform here.

## Cheap text signals (no embeddings)

For a free-text column not worth embedding (see above), cheap derived
numerics still help: string length, word/token count, digit or punctuation
presence/count. Near-zero cost, no model needed.

## Time-based, with cyclical encoding

```python
def engineer_time(df, col):
    dt = pd.to_datetime(df[col])
    return pd.DataFrame({
        f'{col}_hour':       dt.dt.hour,
        f'{col}_dayofweek':  dt.dt.dayofweek,
        f'{col}_is_weekend': dt.dt.dayofweek.isin([5, 6]).astype(int),
        f'{col}_hour_sin':   np.sin(2 * np.pi * dt.dt.hour / 24),
        f'{col}_hour_cos':   np.cos(2 * np.pi * dt.dt.hour / 24),
    })
```

Sin/cos pair matters for anything cyclical (hour, day-of-week, month) — raw
integer encoding tells the model 23:00 and 00:00 are far apart when they're
adjacent.

**Rolling/trailing window aggregates** (e.g. a trailing-N-day mean via
`groupby(...).rolling(...)`) for projects built from raw logs with real
per-row timestamps - not every project has one, so this only applies when
the data step's `build_dataset.py` had actual dates to work with.
Vectorized, so still cheap even at scale.

## Selection

Run `../ml-modeling/scripts/feature_selector.py --file <csv> --target <col>
--top <n>` with `<csv>` = `01-data.json` -> `dataset.train` (or your "Output
table") and `<col>` = `dataset.label` — composite score across variance,
correlation, cardinality, null rate. Use this to justify dropping features, not
just to generate a top-N list.

Done when the feature set is a concrete list (not "relevant features"), each
nontrivial transform - including aggregation and interaction features - is
justified by something in `01-data.md` or the framing (not applied by
default), the file records what was tried and dropped, not just what
survived, and, if this step's feature list resolves a placeholder or
contradicts an assumption in `spec/<topic>.md`, that spec line is updated to
match (see `../ml-modeling/SKILL.md`, "Spec self-staleness").

If this run turns up a bug or a better design in this skill, or you ask for a
change to how it works, log it — see `../ml-modeling/SKILL.md`'s Skill
improvement log.
