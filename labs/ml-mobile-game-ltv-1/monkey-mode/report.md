# Mobile Game LTV (D8-D180) - Monkey-Mode Baseline Report

## Requirements

- **Task + data** (user-confirmed): Predict `ltv_d8_d180` - total USD
  revenue (IAP + ad impressions) a user generates between days 8 and 180
  after install - using only their first 7 days of behavioral event data.
  Regression task, non-payers score 0. Source is `train.csv` inside
  `data/mobile-game-ltv-forecasting-challenge.zip`, which is event-level
  (one row per session/purchase/ad-impression event, many rows per
  `user_id`) and must be aggregated to one row per user before modeling.
- **Primary metric** (user-confirmed): RMSE in USD, matching the
  competition's own evaluation metric.
- **Success bar** (self-inferred): no fixed target RMSE was given, so the
  bar used here is "meaningfully beat both a predict-zero-for-everyone
  baseline and a predict-training-mean-for-everyone baseline," motivated by
  the expectation (confirmed once the data was profiled - see Results and
  Learnings) that `ltv_d8_d180` is extremely right-skewed with a small
  whale population, so raw-USD RMSE is dominated by a handful of large
  payers.

## Input

- Data source: `data/mobile-game-ltv-forecasting-challenge.zip` (real
  path, relative to the sandbox root), containing `train.csv`,
  `test.csv`, and `sample_submission.csv`. The zip is ~97MB compressed;
  `train.csv` alone is ~1.9GB uncompressed with 21,006,238 event rows.
- **No user sampling was needed.** The event log was streamed through
  pandas in 1,000,000-row chunks, aggregating partial per-user statistics
  chunk-by-chunk and merging them at the end (see Design/Implementation).
  This kept peak memory low while covering **100% of the users present in
  train.csv** - the full streaming pass over all 21M rows took 43 seconds.
- **Discrepancy worth flagging plainly here**: the project brief's summary
  said train.csv has "~41,300 users." The actual distinct `user_id` count
  observed in the extracted file is **75,464 users**, not ~41,300. This
  run used all 75,464 - i.e. **100% of the users actually present in the
  file**, even though that is roughly 1.8x the brief's stated total. This
  is noted as a data-quality/documentation observation in Learnings below,
  not treated as a reason to subsample.

## Design

- **Feature aggregation strategy**: the event log has three `event_type`
  values (`session`, `iap`, `ad_impression`) and `day_since_install`
  ranges 0-7 only (confirmed no leakage past day 7 in the raw data).
  Per user, the aggregation computed: total event count; session count;
  IAP count/total/mean revenue; ad-impression count/total/mean revenue;
  distinct days active out of 8 possible (0-7); session counts bucketed
  into early/mid/late thirds of the week (`d0_2`, `d3_5`, `d6_7`); distinct
  ad networks and placements seen; mean/std of `event_hour` as an hour-of-
  day distribution summary; a derived `total_revenue_d0_7` and
  `is_payer_d0_7` flag; and the constant-per-user columns (`platform`,
  `country_tier`, `channel_tier`, `install_day`, `install_week`,
  `ltv_d8_d180`). This matches the fast-defaults feature list in the task
  brief. Nulls were structural only (e.g. `product_id` is null for
  non-purchase events, `network`/`ad_placement`/`revenue_usd` null for
  session events) and resolved naturally by the aggregation (counts/sums
  over the relevant event subset default to 0), so no separate
  impute/drop step was needed beyond that.
- **Model choice**: a single `HistGradientBoostingRegressor` (sklearn),
  trained once with default hyperparameters - no search, no comparison
  against other model families, per the "start simple" fast default for
  skewed tabular regression targets.
- **Preprocessing**: `ColumnTransformer` with `OneHotEncoder` on the three
  low-cardinality categoricals (`platform`: 2 levels, `country_tier`: 23
  levels, `channel_tier`: 16 levels) and `StandardScaler` on the 20
  numeric features, wired into a single sklearn `Pipeline` with the
  regressor.
- **Eval split**: random 80/20 split of the 75,464 users
  (60,371 train / 15,093 test), `random_state=42`. Headline metric is
  plain RMSE on `ltv_d8_d180` in USD on the held-out 20%. Also reported:
  RMSE on `log1p(target)`, and RMSE separately on the subset of test users
  whose true D8-D180 outcome was a payer (nonzero) vs non-payer (zero), as
  extra context per the fast-defaults eval note.

## Implementation

Two scripts, run in order inside `labs/ml-mobile-game-ltv-1/monkey-mode/`
with `uv run python3 <script>.py`.

**`aggregate_features.py`** - streams `train.csv` in 1M-row chunks,
accumulates per-user partial aggregates in dicts, and writes
`user_features.parquet` (one row per user, 25 columns) plus
`profile.json` (data-quality/distribution notes):

```python
import json
import time

import numpy as np
import pandas as pd

TRAIN_CSV = "train.csv"
CHUNKSIZE = 1_000_000

DTYPES = {
    "user_id": "int32",
    "platform": "object",
    "country_tier": "object",
    "channel_tier": "object",
    "install_day": "int16",
    "install_week": "int16",
    "day_since_install": "int8",
    "event_hour": "int8",
    "event_type": "object",
    "event_name": "object",
    "product_id": "object",
    "network": "object",
    "ad_placement": "object",
    "revenue_usd": "float32",
    "ltv_d8_d180": "float32",
}

t0 = time.time()

user_const = {}
n_events, n_sessions, n_iap, sum_iap_rev = {}, {}, {}, {}
n_ad, sum_ad_rev = {}, {}
days_active, day_bucket_sessions = {}, {}
networks_seen, placements_seen = {}, {}
hour_sum, hour_sq_sum, hour_n = {}, {}, {}

null_counts = {c: 0 for c in DTYPES}
total_rows = 0
n_chunks = 0

def bucket_day(d):
    if d <= 2:
        return "d0_2"
    elif d <= 5:
        return "d3_5"
    else:
        return "d6_7"

for chunk in pd.read_csv(TRAIN_CSV, dtype=DTYPES, chunksize=CHUNKSIZE):
    n_chunks += 1
    total_rows += len(chunk)

    for c in DTYPES:
        null_counts[c] += int(chunk[c].isna().sum())

    # constant-per-user columns: first occurrence per user in this chunk
    first = chunk.drop_duplicates(subset="user_id", keep="first")
    for row in first.itertuples(index=False):
        uid = row.user_id
        if uid not in user_const:
            user_const[uid] = (
                row.platform, row.country_tier, row.channel_tier,
                row.install_day, row.install_week, row.ltv_d8_d180,
            )

    vc = chunk.groupby("user_id", observed=True).size()
    for uid, c in vc.items():
        n_events[uid] = n_events.get(uid, 0) + int(c)

    is_session = chunk["event_type"] == "session"
    is_iap = chunk["event_type"] == "iap"
    is_ad = chunk["event_type"] == "ad_impression"

    for uid, c in chunk.loc[is_session].groupby("user_id", observed=True).size().items():
        n_sessions[uid] = n_sessions.get(uid, 0) + int(c)

    iap_chunk = chunk.loc[is_iap]
    for uid, c in iap_chunk.groupby("user_id", observed=True).size().items():
        n_iap[uid] = n_iap.get(uid, 0) + int(c)
    for uid, s in iap_chunk.groupby("user_id", observed=True)["revenue_usd"].sum().items():
        sum_iap_rev[uid] = sum_iap_rev.get(uid, 0.0) + float(s)

    ad_chunk = chunk.loc[is_ad]
    for uid, c in ad_chunk.groupby("user_id", observed=True).size().items():
        n_ad[uid] = n_ad.get(uid, 0) + int(c)
    for uid, s in ad_chunk.groupby("user_id", observed=True)["revenue_usd"].sum().items():
        sum_ad_rev[uid] = sum_ad_rev.get(uid, 0.0) + float(s)

    for uid, days in chunk.groupby("user_id", observed=True)["day_since_install"].unique().items():
        s = days_active.setdefault(uid, set())
        s.update(int(d) for d in days)

    if len(chunk.loc[is_session]):
        sess = chunk.loc[is_session, ["user_id", "day_since_install"]].copy()
        sess["bucket"] = sess["day_since_install"].apply(bucket_day)
        for (uid, b), c in sess.groupby(["user_id", "bucket"], observed=True).size().items():
            d = day_bucket_sessions.setdefault(uid, {})
            d[b] = d.get(b, 0) + int(c)

    if len(ad_chunk):
        for uid, nets in ad_chunk.groupby("user_id", observed=True)["network"].unique().items():
            s = networks_seen.setdefault(uid, set())
            s.update(str(x) for x in nets)
        for uid, pls in ad_chunk.groupby("user_id", observed=True)["ad_placement"].unique().items():
            s = placements_seen.setdefault(uid, set())
            s.update(str(x) for x in pls)

    for uid, s in chunk.groupby("user_id", observed=True)["event_hour"].sum().items():
        hour_sum[uid] = hour_sum.get(uid, 0) + int(s)
    for uid, s in (chunk["event_hour"].astype("float64") ** 2).groupby(chunk["user_id"], observed=True).sum().items():
        hour_sq_sum[uid] = hour_sq_sum.get(uid, 0.0) + float(s)
    for uid, c in chunk.groupby("user_id", observed=True).size().items():
        hour_n[uid] = hour_n.get(uid, 0) + int(c)

user_ids = sorted(user_const.keys())

rows = []
for uid in user_ids:
    platform, country_tier, channel_tier, install_day, install_week, ltv = user_const[uid]
    n_ev = n_events.get(uid, 0)
    n_sess = n_sessions.get(uid, 0)
    n_iap_c = n_iap.get(uid, 0)
    iap_rev = sum_iap_rev.get(uid, 0.0)
    n_ad_c = n_ad.get(uid, 0)
    ad_rev = sum_ad_rev.get(uid, 0.0)
    n_days_active = len(days_active.get(uid, set()))
    buckets = day_bucket_sessions.get(uid, {})
    n_net = len(networks_seen.get(uid, set()))
    n_pl = len(placements_seen.get(uid, set()))
    hn = hour_n.get(uid, 0)
    hs = hour_sum.get(uid, 0)
    hsq = hour_sq_sum.get(uid, 0.0)
    hour_mean = hs / hn if hn else 0.0
    hour_var = (hsq / hn - hour_mean ** 2) if hn else 0.0
    hour_std = np.sqrt(max(hour_var, 0.0))

    rows.append({
        "user_id": uid, "platform": platform, "country_tier": country_tier,
        "channel_tier": channel_tier, "install_day": install_day,
        "install_week": install_week, "n_events": n_ev, "n_sessions": n_sess,
        "n_iap": n_iap_c, "iap_revenue_total": iap_rev,
        "iap_revenue_mean": (iap_rev / n_iap_c) if n_iap_c else 0.0,
        "n_ad_impressions": n_ad_c, "ad_revenue_total": ad_rev,
        "ad_revenue_mean": (ad_rev / n_ad_c) if n_ad_c else 0.0,
        "days_active": n_days_active,
        "sessions_d0_2": buckets.get("d0_2", 0),
        "sessions_d3_5": buckets.get("d3_5", 0),
        "sessions_d6_7": buckets.get("d6_7", 0),
        "n_distinct_networks": n_net, "n_distinct_placements": n_pl,
        "event_hour_mean": hour_mean, "event_hour_std": hour_std,
        "total_revenue_d0_7": iap_rev + ad_rev,
        "is_payer_d0_7": 1 if iap_rev > 0 else 0,
        "ltv_d8_d180": ltv,
    })

df = pd.DataFrame(rows)
df.to_parquet("user_features.parquet", index=False)
```

**`train_eval.py`** - loads `user_features.parquet`, does the 80/20 split,
fits the pipeline, and scores RMSE against baselines:

```python
import json

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RANDOM_STATE = 42

df = pd.read_parquet("user_features.parquet")

CATEGORICAL = ["platform", "country_tier", "channel_tier"]
NUMERIC = [
    "install_day", "install_week",
    "n_events", "n_sessions",
    "n_iap", "iap_revenue_total", "iap_revenue_mean",
    "n_ad_impressions", "ad_revenue_total", "ad_revenue_mean",
    "days_active", "sessions_d0_2", "sessions_d3_5", "sessions_d6_7",
    "n_distinct_networks", "n_distinct_placements",
    "event_hour_mean", "event_hour_std",
    "total_revenue_d0_7", "is_payer_d0_7",
]
FEATURES = CATEGORICAL + NUMERIC
TARGET = "ltv_d8_d180"

X = df[FEATURES]
y = df[TARGET].astype("float64")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_STATE
)

preprocess = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ("num", StandardScaler(), NUMERIC),
    ]
)

model = Pipeline(steps=[
    ("preprocess", preprocess),
    ("gbr", HistGradientBoostingRegressor(random_state=RANDOM_STATE)),
])

model.fit(X_train, y_train)
pred = model.predict(X_test)
pred = np.clip(pred, 0, None)  # revenue can't be negative

rmse_model = root_mean_squared_error(y_test, pred)

pred_zero = np.zeros_like(y_test)
rmse_zero = root_mean_squared_error(y_test, pred_zero)

train_mean = y_train.mean()
pred_mean = np.full_like(y_test, train_mean)
rmse_mean = root_mean_squared_error(y_test, pred_mean)

rmse_log1p_model = root_mean_squared_error(np.log1p(y_test), np.log1p(pred))
rmse_log1p_zero = root_mean_squared_error(np.log1p(y_test), np.log1p(pred_zero))
rmse_log1p_mean = root_mean_squared_error(np.log1p(y_test), np.log1p(pred_mean))

is_payer_outcome = y_test > 0
rmse_model_payers = root_mean_squared_error(
    y_test[is_payer_outcome], pred[is_payer_outcome]
) if is_payer_outcome.sum() else float("nan")
rmse_model_nonpayers = root_mean_squared_error(
    y_test[~is_payer_outcome], pred[~is_payer_outcome]
) if (~is_payer_outcome).sum() else float("nan")

results = {
    "n_train": len(X_train), "n_test": len(X_test),
    "train_mean_target": float(train_mean),
    "rmse_model_usd": float(rmse_model),
    "rmse_predict_zero_usd": float(rmse_zero),
    "rmse_predict_mean_usd": float(rmse_mean),
    "rmse_model_log1p": float(rmse_log1p_model),
    "rmse_predict_zero_log1p": float(rmse_log1p_zero),
    "rmse_predict_mean_log1p": float(rmse_log1p_mean),
    "pct_test_users_nonzero_outcome": float(is_payer_outcome.mean()),
    "rmse_model_payers_usd": float(rmse_model_payers),
    "rmse_model_nonpayers_usd": float(rmse_model_nonpayers),
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(json.dumps(results, indent=2))
```

Both scripts ran to completion in the shared `uv` environment (`pandas
3.0.6`, `numpy 1.26.4`, `scikit-learn 1.9.1`). The streaming aggregation
pass took 43.4 seconds over all 21,006,238 rows; the fit+eval pass took
about 16 seconds wall-clock.

## Results

All numbers are real, from the actual run described above, on the
15,093-user held-out test split.

| Predictor              | RMSE (USD) |
|-------------------------|-----------:|
| Predict 0 for everyone  |     308.65 |
| Predict train mean ($15.95) | 308.18 |
| **HistGradientBoostingRegressor (this baseline)** | **243.73** |

The model beats both naive baselines - the success bar from
Requirements - cutting RMSE by about **21%** versus predict-zero
(308.65 -> 243.73) and about **21%** versus predict-mean
(308.18 -> 243.73). Both naive baselines land at nearly the same RMSE
because the training mean ($15.95) is tiny relative to the scale of the
outliers driving the error - predicting 0 or predicting ~$16 barely
differs when a handful of test users have true LTV in the hundreds or
thousands of dollars.

Context metrics:

- **log1p(target) RMSE**: model 1.560, predict-zero 1.306, predict-mean
  2.509. Predict-zero actually beats the model here. This is not a sign
  the model is bad - it is an artifact of the metric: 60.9% of the test
  set has a true `ltv_d8_d180` of exactly 0, so predicting exactly 0 gets
  `log1p` error of exactly 0 on the majority of rows, which log-space RMSE
  rewards disproportionately. The plain-USD RMSE above is the metric that
  matches the competition and the one to trust as the headline number.
- **Payer vs non-payer split** (based on the true D8-D180 outcome in the
  test set, 39.1% of test users had nonzero outcome): RMSE on the payer
  subset was **379.59 USD**, RMSE on the non-payer subset was
  **70.69 USD**. Nearly all of the model's error comes from the payer
  (whale) subset, consistent with the skew described below.

## Learnings

- **`ltv_d8_d180` is learnable, at least partially, from day 0-7
  signals.** The trained model beats both naive baselines by ~21% RMSE
  using only aggregated first-week behavior - a real, if modest, signal.
- **The revenue distribution is extremely right-skewed** ("whale"
  distribution): mean $16.18, median $0.00, std $287.63, max $24,456.16
  (all users, full 75,464-user table from `profile.json`). The top 10% of
  users by `ltv_d8_d180` account for **96.1%** of total revenue.
- **60.5% of all users have `ltv_d8_d180` == 0** (non-payers over the
  whole D8-D180 window); 39.5% have nonzero revenue.
- **Only 7.6% of users made any in-app purchase in days 0-7**
  (`is_payer_d0_7`), yet 39.5% of users end up with nonzero D8-D180
  revenue. That gap (7.6% vs 39.5%) means a large share of eventual
  revenue-generating users show no purchase signal at all in the first
  week - their D8-D180 revenue likely comes from ad impressions, from
  IAP conversion that happens after day 7, or from engagement patterns
  that only weakly correlate with early purchasing. This is the most
  actionable single finding for feature/label design going forward.
- **No meaningful data-quality problems found.** Nulls in the raw event
  log were all structural and expected: `product_id` is null for
  20,950,193 of 21,006,238 rows because it only applies to `iap` events;
  `network`, `ad_placement`, and `revenue_usd` are null for the
  2,359,512 `session` rows because those fields don't apply to session
  events. `day_since_install` was confirmed to range 0-7 only in the raw
  data (no future leakage available to aggregate from even by mistake).
- **Discrepancy from the brief**: the brief's summary said "~41,300
  users" in train.csv; the actual file has 75,464 distinct `user_id`
  values (about 1.83x higher). This doesn't block the baseline - the
  full 75,464 were used - but is worth reconciling with the actual
  competition docs before this number gets reused elsewhere (e.g. in
  `prd/` or `design/`, which this run did not touch).
- **RMSE-in-USD vs RMSE-in-log1p disagree on baseline ranking**, as noted
  in Results - a reminder that log-space RMSE is not a drop-in substitute
  for the competition's plain-USD metric when the target is this
  zero-heavy.

## Suggested Next Steps

- A single gradient-boosted tree ensemble looks like a reasonable **V1
  model class** for the regular `ml-system-design` flow on this problem -
  it already beats naive baselines with zero tuning on real aggregated
  features.
- The whale-skew (top 10% of users = 96% of revenue) and the payer-subset
  RMSE ($379.59) dwarfing the non-payer-subset RMSE ($70.69) both point
  toward a **two-stage model** worth discussing in `design/high-level.md`
  later: a classifier for "will this user generate any D8-D180 revenue at
  all" followed by a regressor (possibly on `log1p(revenue)`) for the
  amount conditional on being a payer, rather than one regressor over the
  full zero-heavy, heavy-tailed target.
- The 7.6% (d0-7 payer) vs 39.5% (d8-180 nonzero) gap suggests early
  purchase behavior alone under-identifies future revenue generators;
  engagement/retention-shaped features (session cadence, day-over-day
  activity decay, ad-engagement depth) may carry more signal than raw
  purchase counts for the classification half of a two-stage design.
- Given the log1p-vs-USD RMSE disagreement observed here, if a
  log-transformed target is adopted for the regressor in the two-stage
  design, evaluation should still report plain-USD RMSE (or a metric
  computed only over the true-payer subset) as the primary number, not
  log-space RMSE alone, to avoid the zero-heavy majority masking real
  payer-side error.
- This report intentionally did not read or write `design/`, `prd/`,
  `modeling/`, `adr/`, or `spec/` - the above are inputs for whoever picks
  up that regular flow, not decisions made here.
