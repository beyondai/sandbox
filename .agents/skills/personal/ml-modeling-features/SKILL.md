---
name: ml-modeling-features
description: >-
  Use to engineer and select features for an ML model - numerical transforms,
  categorical encoding, leave-one-out aggregation features, interaction/cross
  features, time-based/cyclical features, importance-based selection. Step 2
  of the ml-modeling-* chain (data → features → train → evaluate → serve).
  Trigger on
  "engineer features for this," "encode these columns," or continuing
  modeling work in an existing ML project folder.
---

# Engineer Features

Contents: Numerical transforms | Categorical encoding | Aggregation features
(leave-one-out) | Embeddings | Interaction and cross features | Cheap text
signals | Time-based, with cyclical encoding | Selection | Check

- **Reads:** the ML framing in `<project-folder>/design/high-level.md`
  (population, unit of prediction: what one row is) and
  `modeling/01-data.md` (profile, risk flags).
- **Input table:** `01-data.json` -> `dataset.train`. Never open
  `dataset.test` here.
- **Writes:** `modeling/02-features.md` and `modeling/features.py` with
  `transform(df)`, fit on train only; evaluate applies the same function
  to test (see "Handoff" in `../ml-modeling/SKILL.md`). A transformed
  train table goes in `modeling/datasets/`, and its path goes under
  "Output table" in `02-features.md`, so train uses it.
- **Aggregates from raw logs** (counts, recency, trends over events) need
  the event rows, so `build_dataset.py` (data step) builds the base
  aggregates. This step decides which to keep and how to transform them.
- **Rules:** `../ml-system-design/SKILL.md`, "Project folder", "Output
  docs", "Check the output", "Skill improvement log".
- **Mode:** Regular proposes transforms from the profile and the framing,
  and checks importance before it decides. Quick POC selects the most
  useful transforms and continues.

The feature list is this step's decision. Each transform needs a reason
in `01-data.md` or in the framing. Apply none by default.

Steps:
1. Run "Design docs changed?" in `../ml-modeling/SKILL.md`.
2. Select transforms from the sections below.
3. Run the selection script.
4. Write `02-features.md`: the list, the reason for each transform, and
   what was tried and dropped.
5. Check.

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

- **Missing flags.** For a numeric column with a real null rate, add a
  binary `{col}_missing`. The signal stays after imputation.
- **Skewed column.** Use `pd.qcut` (quantile bins), not `pd.cut`. Fixed
  bins put almost all rows in one bin.

## Categorical encoding

- Low cardinality: one-hot.
- High cardinality (for example `user_id`): target or frequency encoding.
- Target encoding is smoothed:
  `smoothed = (count * cat_mean + k * global_mean) / (count + k)`. A rare
  category moves toward the global mean.

## Aggregation features (leave-one-out)

Statistics for each entity of the population (user, item, session): the
mean, count, or std of the target or of a numeric column. Often the
strongest group, and cheap (one groupby).

**Leave-one-out is mandatory when the statistic uses the row's own
label.** Without it, the label leaks into its own feature.

```python
count = df.groupby(entity_col)[target_col].transform('count')
total = df.groupby(entity_col)[target_col].transform('sum')
loo_rate = (total - df[target_col]) / (count - 1)
loo_rate = loo_rate.fillna(df[target_col].mean())  # count == 1 groups
```

- Keep the count next to the rate. A rate from 2 rows is less reliable
  than a rate from 2,000.
- Save a lookup table (`<entity id> -> rate, count`). Train and evaluate
  **left-join** it onto the test split. Test rows are not in the train
  statistic, so a plain join does not leak.
- **k-fold CV.** A column computed once before the split leaks across
  the rows of a validation fold that share an entity. A boosted model uses
  this leak more than a linear or bagged model, so the CV winner can be
  wrong. Compute the column again in each fold (leave-one-out in the train
  part, left-join onto the validation part). If you do not, mark the CV
  ranking as provisional until `ml-modeling-evaluate`.

## Embeddings

Not used, in both modes. A POC has no time to train or fine-tune them, and
a generic pretrained embedding is not adapted to the task. A local
embedding model is on hold (laptop resources). Use frequency or target
encoding for categoricals and IDs. For free text, use "Cheap text
signals".

## Interaction and cross features

Combine 2 or 3 categorical columns, or take a ratio or product of 2
related numeric columns. Do this only when the profile or the domain shows
a joint effect. Do not generate all combinations.

## Cheap text signals

For a free-text column: string length, token count, digit and punctuation
counts. No model is necessary.

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

- Use the sin/cos pair for each cyclical value (hour, day of week, month).
  A raw integer puts 23:00 far from 00:00.
- Trailing-window aggregates (for example a trailing N-day mean with
  `groupby(...).rolling(...)`): only when `build_dataset.py` had real row
  timestamps.

## Selection

Run:

```
python3 .agents/skills/personal/ml-modeling/scripts/feature_selector.py --file <csv> --target <col> --top <n>
```

`<csv>` is `dataset.train` (or the "Output table"). `<col>` is
`dataset.label`. The score combines variance, correlation, cardinality,
and null rate. It is a rough screen: remove the id column first, and do
not drop a feature on this score alone. Confirm a drop with model
importance or a CV ablation.

## Check

Do "Check the output" in `../ml-system-design/SKILL.md`. Intent questions:
1. Is the feature set a concrete list, not "relevant features"?
2. Does each transform (aggregation and interaction included) have a
   reason in `01-data.md` or in the framing?
3. Is each feature available at prediction time? Does each aggregate that
   uses the label use leave-one-out (and per fold for CV)?
4. Does the file record what was tried and dropped?

Done when the 4 answers are yes, `check_doc.py` prints `OK`, and a spec
line that this feature list resolves or contradicts is updated (see
"Closing the loop" in `../ml-modeling/SKILL.md`).
