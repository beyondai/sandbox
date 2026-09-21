"""Build labeled lapse/revival tables from the lifecycle logs.

Label and population rules come from design/deep-dive.md (Training section).
Features use only activity strictly before the cutoff; labels use only
activity at or after it. Run: uv run python3 modeling/build_dataset.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / "data/riot-synthetic/synthetic-data/data/lifecycle"
OUT = Path(__file__).resolve().parent / "datasets"

LAPSE_H = 28
REVIVAL_H = 14
TRAIN_CUTOFF = 135
TEST_CUTOFF = 180

# From design/deep-dive.md; a mismatch here means the label logic drifted or
# leaked (an earlier draft leaked future activity and got 100% churn).
EXPECTED = {
    ("lapse", TRAIN_CUTOFF): (4954, 0.0820),
    ("lapse", TEST_CUTOFF): (4675, 0.0868),
    ("revival", TRAIN_CUTOFF): (5181, 0.0365),
    ("revival", TEST_CUTOFF): (5719, 0.0259),
}


def load():
    players = pd.read_csv(RAW / "players.csv")
    players["region"] = players["region"].fillna("unknown")
    activity = pd.read_csv(RAW / "activity.csv")
    campaign = pd.read_csv(RAW / "campaign.csv")
    calendar = pd.read_csv(RAW / "content_calendar.csv")
    treated = set(campaign.loc[campaign.treated == 1, "player_id"])
    return players, activity, calendar, treated


def days_to_nearest_event(cutoff, calendar):
    return int((calendar.start_day - cutoff).abs().min())


def window_aggregates(act, prefix):
    g = act.groupby("player_id")
    out = pd.DataFrame(
        {
            f"{prefix}active_days": g.day.nunique(),
            f"{prefix}games": g.games.sum(),
            f"{prefix}wins": g.wins.sum(),
            f"{prefix}party_games": g.party_games.sum(),
            f"{prefix}minutes": g.minutes.sum(),
        }
    )
    out[f"{prefix}win_rate"] = out[f"{prefix}wins"] / out[f"{prefix}games"].replace(0, np.nan)
    out[f"{prefix}party_share"] = out[f"{prefix}party_games"] / out[f"{prefix}games"].replace(0, np.nan)
    out[f"{prefix}avg_minutes_per_active_day"] = out[f"{prefix}minutes"] / out[f"{prefix}active_days"]
    return out.drop(columns=[f"{prefix}wins", f"{prefix}party_games"])


def build_lapse(cutoff, players, activity, calendar, treated, exclude_treated):
    pre = activity[activity.day < cutoff]
    post = activity[(activity.day >= cutoff) & (activity.day < cutoff + LAPSE_H)]
    last_active = pre.groupby("player_id").day.max()
    pop = last_active[last_active >= cutoff - 7].index
    if exclude_treated:
        pop = pop[~pop.isin(treated)]

    trailing_28 = window_aggregates(pre[pre.day >= cutoff - 28], "")
    trailing_7 = pre[pre.day >= cutoff - 7].groupby("player_id").agg(games_7=("games", "sum"), wins_7=("wins", "sum"))
    trailing_7["recent_loss_rate_7"] = 1 - trailing_7.wins_7 / trailing_7.games_7.replace(0, np.nan)

    df = players.set_index("player_id").loc[pop, ["signup_day", "region", "platform", "acquisition_source"]].copy()
    df = df.join(trailing_28).join(trailing_7[["recent_loss_rate_7"]])
    df["tenure_days"] = cutoff - df.signup_day
    df["days_since_last_active"] = cutoff - last_active.loc[pop]
    df["days_to_nearest_content_event"] = days_to_nearest_event(cutoff, calendar)
    df["cutoff"] = cutoff
    df["lapsed"] = (~df.index.isin(post.player_id.unique())).astype(int)
    return df.drop(columns=["signup_day"]).reset_index()


def build_revival(cutoff, players, activity, calendar, treated, exclude_treated):
    pre = activity[activity.day < cutoff]
    post = activity[(activity.day >= cutoff) & (activity.day < cutoff + REVIVAL_H)]
    signup = players.set_index("player_id").signup_day
    last_active = pre.groupby("player_id").day.max()

    eligible = signup[signup < cutoff - 7].index
    la = last_active.reindex(eligible)
    pop = la[(la < cutoff - 7) | la.isna()].index
    if exclude_treated:
        pop = pop[~pop.isin(treated)]

    lifetime = window_aggregates(pre, "lifetime_")
    df = players.set_index("player_id").loc[pop, ["signup_day", "region", "platform", "acquisition_source"]].copy()
    df = df.join(lifetime)
    la_pop = last_active.reindex(pop)
    df["days_since_last_active"] = cutoff - la_pop  # NaN if never played
    df["tenure_at_lapse"] = la_pop - df.signup_day
    df["never_played"] = la_pop.isna().astype(int)
    df["days_to_nearest_content_event"] = days_to_nearest_event(cutoff, calendar)
    df["cutoff"] = cutoff
    df["returned"] = df.index.isin(post.player_id.unique()).astype(int)
    return df.drop(columns=["signup_day"]).reset_index()


def check(name, cutoff, df, label):
    n, rate = len(df), df[label].mean()
    exp_n, exp_rate = EXPECTED[(name, cutoff)]
    assert n == exp_n, f"{name}@{cutoff}: n={n}, expected {exp_n}"
    assert abs(rate - exp_rate) < 5e-4, f"{name}@{cutoff}: rate={rate:.4f}, expected {exp_rate}"
    print(f"{name:8s} cutoff={cutoff} n={n} positive_rate={rate:.4f}  ok")


def main():
    OUT.mkdir(exist_ok=True)
    players, activity, calendar, treated = load()
    for name, builder, label in [("lapse", build_lapse, "lapsed"), ("revival", build_revival, "returned")]:
        for split, cutoff in [("train", TRAIN_CUTOFF), ("test", TEST_CUTOFF)]:
            df = builder(cutoff, players, activity, calendar, treated, exclude_treated=(cutoff == TEST_CUTOFF))
            check(name, cutoff, df, label)
            df.to_csv(OUT / f"{name}_{split}.csv", index=False)


if __name__ == "__main__":
    main()
