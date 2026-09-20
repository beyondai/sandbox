---
name: ml-modeling-features
description: Use to engineer and select features for an ML model — numerical transforms, categorical encoding, time-based/cyclical features, importance-based selection. Step 2 of the ml-modeling-* chain (data → features → train → evaluate). Trigger on "engineer features for this," "encode these columns," or continuing modeling work in an existing ml-<topic>-<n>/ project.
---

# Engineer Features

Reads `<project-folder>/design/deep-dive.md`'s Features section (required) and
`modeling/01-data.md` (the risk flags from the profiling step). Writes
`<project-folder>/modeling/02-features.md`. First, run the "Deep-dive changed?"
check from `../ml-modeling/SKILL.md`.

Mode: Regular tries the transforms `design/deep-dive.md` named and checks
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

## Categorical encoding

One-hot for low cardinality; target or frequency encoding for high-cardinality
columns (e.g. `user_id`) — one-hot there would blow up dimensionality.

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

## Selection

Run `../ml-modeling/scripts/feature_selector.py --file <csv> --target <col>
--top <n>` — composite score across variance, correlation, cardinality, null
rate. Use this to justify dropping features, not just to generate a top-N list.

Done when the feature set is a concrete list (not "relevant features"), each
nontrivial transform is justified by something in `01-data.md` or `deep-dive.md`
(not applied by default), and the file records what was tried and dropped, not
just what survived.

If this run turns up a bug or a better design in this skill, or you ask for a
change to how it works, log it — see `../ml-modeling/SKILL.md`'s Skill
improvement log.
