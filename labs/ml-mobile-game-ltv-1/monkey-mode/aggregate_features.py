"""
Aggregate the event-level train.csv (one row per user event) into a
one-row-per-user_id feature table for the mobile-game LTV baseline.

Reads the ~1.9GB train.csv in chunks (memory-safe, no need to hold the
full 21M-row event log in memory at once), computes per-chunk partial
aggregates keyed by user_id, and combines them at the end. This lets us
use the FULL set of users (no sampling needed) while keeping peak memory
low.

Outputs:
  - user_features.parquet : one row per user_id, engineered features
  - profile.json          : data-quality / distribution notes for report.md
"""
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

# Partial state accumulated across chunks
user_const = {}  # user_id -> (platform, country_tier, channel_tier,
                  #             install_day, install_week, ltv_d8_d180)
n_events = {}
n_sessions = {}
n_iap = {}
sum_iap_rev = {}
n_ad = {}
sum_ad_rev = {}
days_active = {}  # user_id -> set of day_since_install seen
day_bucket_sessions = {}  # user_id -> dict{bucket: count} for session events
networks_seen = {}  # user_id -> set of network (ad events)
placements_seen = {}  # user_id -> set of ad_placement (ad events)
hour_sum = {}
hour_sq_sum = {}
hour_n = {}

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

    # constant-per-user columns: take first occurrence per user in this chunk
    first = chunk.drop_duplicates(subset="user_id", keep="first")
    for row in first.itertuples(index=False):
        uid = row.user_id
        if uid not in user_const:
            user_const[uid] = (
                row.platform,
                row.country_tier,
                row.channel_tier,
                row.install_day,
                row.install_week,
                row.ltv_d8_d180,
            )

    # event counts
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

    # days active (distinct day_since_install per user)
    for uid, days in chunk.groupby("user_id", observed=True)["day_since_install"].unique().items():
        s = days_active.setdefault(uid, set())
        s.update(int(d) for d in days)

    # session counts by day bucket
    if len(chunk.loc[is_session]):
        sess = chunk.loc[is_session, ["user_id", "day_since_install"]].copy()
        sess["bucket"] = sess["day_since_install"].apply(bucket_day)
        for (uid, b), c in sess.groupby(["user_id", "bucket"], observed=True).size().items():
            d = day_bucket_sessions.setdefault(uid, {})
            d[b] = d.get(b, 0) + int(c)

    # distinct networks / placements seen (ad events only)
    if len(ad_chunk):
        for uid, nets in ad_chunk.groupby("user_id", observed=True)["network"].unique().items():
            s = networks_seen.setdefault(uid, set())
            s.update(str(x) for x in nets)
        for uid, pls in ad_chunk.groupby("user_id", observed=True)["ad_placement"].unique().items():
            s = placements_seen.setdefault(uid, set())
            s.update(str(x) for x in pls)

    # hour-of-day distribution summary (mean/std via sum and sum-of-squares)
    for uid, s in chunk.groupby("user_id", observed=True)["event_hour"].sum().items():
        hour_sum[uid] = hour_sum.get(uid, 0) + int(s)
    for uid, s in (chunk["event_hour"].astype("float64") ** 2).groupby(chunk["user_id"], observed=True).sum().items():
        hour_sq_sum[uid] = hour_sq_sum.get(uid, 0.0) + float(s)
    for uid, c in chunk.groupby("user_id", observed=True).size().items():
        hour_n[uid] = hour_n.get(uid, 0) + int(c)

    print(f"  chunk {n_chunks}: {total_rows:,} rows processed "
          f"({time.time() - t0:.1f}s elapsed)", flush=True)

print(f"Finished streaming pass: {total_rows:,} rows, {n_chunks} chunks, "
      f"{time.time() - t0:.1f}s", flush=True)

user_ids = sorted(user_const.keys())
print(f"Distinct users: {len(user_ids):,}", flush=True)

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
        "user_id": uid,
        "platform": platform,
        "country_tier": country_tier,
        "channel_tier": channel_tier,
        "install_day": install_day,
        "install_week": install_week,
        "n_events": n_ev,
        "n_sessions": n_sess,
        "n_iap": n_iap_c,
        "iap_revenue_total": iap_rev,
        "iap_revenue_mean": (iap_rev / n_iap_c) if n_iap_c else 0.0,
        "n_ad_impressions": n_ad_c,
        "ad_revenue_total": ad_rev,
        "ad_revenue_mean": (ad_rev / n_ad_c) if n_ad_c else 0.0,
        "days_active": n_days_active,
        "sessions_d0_2": buckets.get("d0_2", 0),
        "sessions_d3_5": buckets.get("d3_5", 0),
        "sessions_d6_7": buckets.get("d6_7", 0),
        "n_distinct_networks": n_net,
        "n_distinct_placements": n_pl,
        "event_hour_mean": hour_mean,
        "event_hour_std": hour_std,
        "total_revenue_d0_7": iap_rev + ad_rev,
        "is_payer_d0_7": 1 if iap_rev > 0 else 0,
        "ltv_d8_d180": ltv,
    })

df = pd.DataFrame(rows)
df.to_parquet("user_features.parquet", index=False)
print(f"Wrote user_features.parquet: {df.shape}", flush=True)

# ---- profiling info for report.md ----
target = df["ltv_d8_d180"]
profile = {
    "total_event_rows": int(total_rows),
    "n_chunks": n_chunks,
    "elapsed_seconds": round(time.time() - t0, 1),
    "n_users": len(df),
    "null_counts_raw_columns": null_counts,
    "target_stats": {
        "mean": float(target.mean()),
        "median": float(target.median()),
        "std": float(target.std()),
        "min": float(target.min()),
        "max": float(target.max()),
        "p90": float(target.quantile(0.90)),
        "p99": float(target.quantile(0.99)),
        "p999": float(target.quantile(0.999)),
    },
    "pct_zero_target": float((target == 0).mean()),
    "pct_nonzero_target": float((target > 0).mean()),
    "pct_payer_d0_7": float(df["is_payer_d0_7"].mean()),
    "top10_target_sum_share": float(
        target.sort_values(ascending=False).head(int(len(df) * 0.10)).sum() / target.sum()
    ) if target.sum() > 0 else 0.0,
}
with open("profile.json", "w") as f:
    json.dump(profile, f, indent=2)
print(json.dumps(profile, indent=2))
