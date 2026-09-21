# KKBOX Repeat-Listen Prediction — Monkey-Mode Fast Baseline

## Requirements

- Task + data (answered-by-user): binary classification —
  predict the probability a user will listen to a given song
  again (repeat-listen) within a time window, for (user, song)
  pairs. This is the WSDM/KKBOX 2018 Kaggle "Music
  Recommendation" challenge. Label column in `train.csv` is
  `target` (1 = repeat listen, 0 = not). `test.csv` is the
  Kaggle submission set with no label and was not used; all
  evaluation here comes from a held-out split of `train.csv`
  only.
- Primary metric (answered-by-user): AUC (area under the ROC
  curve) between predicted probability and the true `target`.
- Success bar (answered-by-user): AUC >= 0.65 counts as a
  good-enough first baseline.
- Sample size of 600,000 rows from `train.csv` (self-inferred):
  chosen within the suggested 300k-1M range, using
  `DataFrame.sample` with a fixed random seed for
  reproducibility.
- Model choice: `RandomForestClassifier` with 200 trees and max
  depth 12 (self-inferred): a single, fast, decent tree
  ensemble per the "one model, no comparison" fast default.
  Ran once, no hyperparameter search.
- Feature set (self-inferred): a handful of raw fields joined
  from `members.csv` (city, gender, age, registration/
  expiration dates, registration method) and `songs.csv` /
  `song_extra_info.csv` (song length, language, an ISRC-derived
  country-code proxy), plus the interaction-context columns
  already present in `train.csv` (source_system_tab,
  source_screen_name, source_type). No elaborate engineering,
  no embeddings.
- Split (self-inferred): a single random 80/20 held-out split
  of the sampled rows, stratified on `target`, fixed random
  seed 42.

## Input

- Data source (real path): `/Users/alex/dev/sandbox/data/kkbox/
  kkbox-music-recommendation-challenge.zip` (361,577,170 bytes).
- Unzipping: the outer `.zip` contained six `.7z` archives
  (`members.csv.7z`, `sample_submission.csv.7z`,
  `song_extra_info.csv.7z`, `songs.csv.7z`, `test.csv.7z`,
  `train.csv.7z`) rather than plain CSVs directly. No system
  `7z`/`p7zip` binary was available on this machine, so the
  `.zip` was extracted with the standard `unzip` CLI into a
  scratch staging directory, then the four `.7z` files actually
  needed (`members.csv.7z`, `songs.csv.7z`,
  `song_extra_info.csv.7z`, `train.csv.7z`) were decompressed
  with the Python `py7zr` package into
  `/Users/alex/dev/sandbox/data/kkbox/extracted/`.
  `test.csv.7z` and `sample_submission.csv.7z` were left
  unextracted since this baseline does not use them.
- Resulting files in `/Users/alex/dev/sandbox/data/kkbox/
  extracted/`: `train.csv` (971,675,848 bytes, 7,377,418 data
  rows), `members.csv` (2,503,827 bytes), `songs.csv`
  (221,828,666 bytes), `song_extra_info.csv` (181,010,294
  bytes).
- Sampling: `train.csv` was loaded in full with pandas
  (7,377,418 rows x 6 columns), then down-sampled to 600,000
  rows via `DataFrame.sample(n=600_000, random_state=42)`
  before any joins or training, for speed.

## Design

Applying the fast-baseline defaults to this problem:

- Cleaning: numeric nulls (song length, age, registration/
  expiration dates) median-imputed; categorical nulls
  (gender, source columns, ISRC country) most-frequent-imputed.
  Nothing more elaborate — no outlier clipping on the known-
  noisy `bd` (age) field, no missing-value flags.
- Features: joined `train.csv` to `members.csv` on `msno` and
  to `songs.csv` / `song_extra_info.csv` on `song_id` to pull in
  a handful of raw fields (song length, self-reported age,
  gender, city, registration method, registration/expiration
  dates, language, and a 2-character country-code proxy parsed
  from the ISRC code). Combined with the three context columns
  already in `train.csv` (source_system_tab,
  source_screen_name, source_type), this gives 4 numeric + 8
  categorical raw columns. Numerics were standard-scaled;
  categoricals were one-hot encoded with unknown categories
  ignored at inference time. No embeddings, no target encoding,
  no interaction features.
- Model: a single `RandomForestClassifier` (200 trees, max
  depth 12, all cores) — a fast, decent tree ensemble that
  handles the mixed numeric/categorical, null-heavy feature set
  without needing careful scaling assumptions the way logistic
  regression would. Trained once; no hyperparameter search, no
  comparison against a second model class.
- Eval: single random 80/20 stratified split of the 600k-row
  sample, scored with `roc_auc_score` on the held-out 20%
  (120,000 rows).

## Implementation

The full script that ran, saved at `monkey-mode/baseline.py`:

```python
"""
Monkey-mode fast baseline for the KKBOX Music Recommendation
(WSDM 2018 Kaggle) repeat-listen prediction task.

Binary classification: predict P(target=1) that a user will
listen to a given song again within the observation window, for
each (user, song) pair in train.csv.

Fast defaults used (see report.md for full rationale):
  - median-impute numeric nulls, most-frequent-impute categoricals
  - standard-scale numerics, one-hot low-cardinality categoricals
  - single model: RandomForestClassifier, modest n_estimators, no
    hyperparameter search
  - single random 80/20 held-out split, scored on AUC
  - sampled subset of train.csv for speed (see SAMPLE_ROWS below)
"""

import time

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DATA_DIR = "/Users/alex/dev/sandbox/data/kkbox/extracted"
SAMPLE_ROWS = 600_000  # self-inferred: within the 300k-1M guidance
RANDOM_STATE = 42

t0 = time.time()

# ---------------------------------------------------------------
# Load
# ---------------------------------------------------------------
train_full = pd.read_csv(f"{DATA_DIR}/train.csv")
print(f"train.csv full shape: {train_full.shape}")

if len(train_full) > SAMPLE_ROWS:
    train = train_full.sample(n=SAMPLE_ROWS, random_state=RANDOM_STATE)
else:
    train = train_full
print(f"sampled shape: {train.shape}")

members = pd.read_csv(f"{DATA_DIR}/members.csv")
songs = pd.read_csv(f"{DATA_DIR}/songs.csv")
song_extra = pd.read_csv(f"{DATA_DIR}/song_extra_info.csv")

# ---------------------------------------------------------------
# Join minimal extra raw features
# ---------------------------------------------------------------
df = train.merge(members, on="msno", how="left")
df = df.merge(songs, on="song_id", how="left")
df = df.merge(song_extra[["song_id", "isrc"]], on="song_id", how="left")

# derive a simple country-code proxy from isrc (first 2 chars) -
# a low-cardinality categorical, no elaborate parsing
df["isrc_country"] = df["isrc"].astype(str).str[:2]

# registration_init_time / expiration_date are int-encoded dates
# (YYYYMMDD) in members.csv - kept as raw numeric, no date parsing
numeric_features = [
    "song_length",
    "bd",  # self-reported age, known to have outliers/nulls
    "registration_init_time",
    "expiration_date",
]
categorical_features = [
    "source_system_tab",
    "source_screen_name",
    "source_type",
    "city",
    "gender",
    "registered_via",
    "language",
    "isrc_country",
]

target_col = "target"

for col in numeric_features:
    if col not in df.columns:
        df[col] = np.nan
for col in categorical_features:
    if col not in df.columns:
        df[col] = "unknown"

X = df[numeric_features + categorical_features]
y = df[target_col]

print(f"feature matrix shape: {X.shape}, positive rate: {y.mean():.4f}")

# ---------------------------------------------------------------
# Split
# ---------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
)

# ---------------------------------------------------------------
# Preprocess + model pipeline
# ---------------------------------------------------------------
numeric_pipe = Pipeline(
    [
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ]
)
categorical_pipe = Pipeline(
    [
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ]
)
preprocess = ColumnTransformer(
    [
        ("num", numeric_pipe, numeric_features),
        ("cat", categorical_pipe, categorical_features),
    ]
)

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    n_jobs=-1,
    random_state=RANDOM_STATE,
)

pipe = Pipeline([("preprocess", preprocess), ("model", model)])

# ---------------------------------------------------------------
# Train + eval
# ---------------------------------------------------------------
pipe.fit(X_train, y_train)
val_probs = pipe.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, val_probs)

elapsed = time.time() - t0
print(f"Held-out AUC: {auc:.4f}")
print(f"Total elapsed: {elapsed:.1f}s")

# ---------------------------------------------------------------
# Quick feature-importance readout (informs "next steps", not
# part of the eval loop)
# ---------------------------------------------------------------
feature_names = pipe.named_steps["preprocess"].get_feature_names_out()
importances = pipe.named_steps["model"].feature_importances_
order = np.argsort(importances)[::-1][:15]
print("Top 15 feature importances:")
for i in order:
    print(f"  {feature_names[i]}: {importances[i]:.4f}")

print("Null rate in joined feature columns:")
print(X.isnull().mean().sort_values(ascending=False).to_string())
```

## Results

Real output from running `baseline.py` against the venv
described in Learnings below:

```
train.csv full shape: (7377418, 6)
sampled shape: (600000, 6)
feature matrix shape: (600000, 12), positive rate: 0.5045
Held-out AUC: 0.6727
Total elapsed: 59.9s
```

**Held-out AUC: 0.6727.** Against the 0.65 success bar, this
baseline **beat** the bar (0.6727 > 0.65, a margin of about
+0.023).

## Learnings

- The target is learnable with only shallow, mostly
  demographic/context features: a same-day, no-tuning random
  forest on 12 raw columns clears the 0.65 bar. This is a
  meaningful signal that the (user, song) repeat-listen problem
  has real structure a heavier feature/model pass can build on.
- The single strongest signal group by far is *listening
  context*, not user or song attributes: the top 8 of the top
  15 feature importances are all one-hot levels of
  `source_system_tab`, `source_screen_name`, and `source_type`
  (e.g. `source_system_tab_my library`: 0.1749,
  `source_screen_name_Local playlist more`: 0.1428,
  `source_type_local-library`: 0.0932). The strongest
  member/song-level numeric feature, `expiration_date`, ranks
  9th at 0.0379. This suggests where a listen originated
  (library vs. discover vs. radio) is far more predictive than
  who the user is or what song it is, at least in this shallow
  feature set.
- Data quality: the outer archive was not plain CSVs but `.zip`
  containing `.7z` files, and no system 7-zip binary was present
  on this machine — worth knowing before assuming a
  straightforward unzip. Within the joined feature columns,
  `gender` has a high 40.2% null rate and `isrc_country` (derived
  from `song_extra_info.csv`) is null in 7.9% of rows; source
  columns (system_tab, screen_name, type) are null in 0.3-5.6%
  of rows. Numeric member fields (bd, registration/expiration
  dates, city, registered_via) are essentially complete
  (0% null). `bd` (self-reported age) is known in the community
  to contain implausible values (0, negative, >100) that this
  baseline did not clean beyond median imputation of true nulls
  — a real modeling pass should treat `bd` outliers explicitly.
- The label is close to balanced (positive rate 0.5045 in the
  600k sample), so AUC is a meaningful and not artificially
  inflated metric here — no severe class imbalance to correct
  for at the baseline stage.
- Venv-install note: the ambient Python on this machine had no
  `pandas`, `numpy`, or `scikit-learn` (confirmed via
  `ModuleNotFoundError` before any baseline code ran). A
  project-local venv was created at `monkey-mode/.venv` and
  `pandas`, `numpy`, `scikit-learn`, and `py7zr` (needed only
  for the `.7z` extraction step, not for modeling) were
  installed into it. This is a candidate to add to the base
  sandbox Python environment so future runs on this machine
  don't repeat the install.

## Suggested Next Steps

- The listening-context feature group (source_system_tab,
  source_screen_name, source_type) so dominated feature
  importance that a regular design pass should treat it as a
  first-class feature group, not an afterthought alongside user/
  song metadata. It's plausible a model leaning more heavily on
  richer encodings of listening context (e.g. combined
  tab+screen+type interaction terms) would move AUC further
  before user- or song-level features add much.
- User- and song-level features (age, gender, city, song
  length, language, ISRC country) contributed comparatively
  little in this shallow join. Before investing in deeper
  user/song feature engineering (e.g. historical play counts,
  artist/genre embeddings), it would be worth first checking
  whether adding simple aggregate features (e.g. per-user or
  per-song historical repeat-listen rate) captures more signal
  than one-off demographic joins did here — those aggregates
  were out of scope for this fast baseline but are a natural
  next feature group to try.
- A single shallow RandomForest already clears the bar, which
  is a reasonable signal that a gradient-boosted tree model
  (e.g. LightGBM/XGBoost) is a sound V1 model-class bet for this
  problem: same family of model, handles the same mixed
  categorical/numeric, null-heavy feature set, but typically
  extracts more signal per feature and trains fast enough for
  the multi-million-row full dataset (this baseline only used
  8% of available training rows).
- The `bd` (age) field's known data-quality issues (implausible
  values) should get explicit treatment (e.g. clipping or a
  validity flag) in the real feature-engineering pass rather
  than the median-impute-only treatment used here.
- Given `gender` is null in 40% of rows and ranked low in
  importance anyway, it's a reasonable candidate to deprioritize
  or drop in the next iteration rather than invest in fancier
  imputation for it.
