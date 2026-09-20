#!/usr/bin/env python3
"""
riot_practice_data.py - synthetic, Riot-flavored practice datasets with hidden ground truth.

Why synthetic: you know the true parameters and even the true counterfactuals, so you can
check whether your from-scratch system RECOVERS them before trusting any metric.

Usage (numpy + pandas only):
    uv run python riot_practice_data.py --out data/sim --seed 0            # all datasets
    uv run python riot_practice_data.py --out data/sim --seed 3 --only lifecycle

Each folder has a `_truth/` subfolder = the answer key. Do NOT open it while modeling;
use it only in the final "did I recover it?" check.

Priority for the Player Intelligence & Personalization role:
    lifecycle/  270 days of players: activity, purchases, content events, and a randomized
                win-back/offer campaign on day 180 -> churn, revival, LTV, uplift / next-best-action
    shop/       skin purchases, champion play, and a 6-slot storefront impression log
                -> recommendation, item-to-item, learning-to-rank with position bias
    newplayer/  first 4 weeks of new players -> early churn (optional)
    ranked/     5v5 ranked matches -> skill rating / matchmaking (optional)

Change --seed for a fresh draw on every practice rep.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def _softmax(z):
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


# --------------------------------------------------------------------------- ranked
def sim_ranked(rng, n_players=3000, n_matches=40_000, team_size=5,
               smurf_frac=0.02, beta=0.5, mm_noise=0.8):
    """5v5 matches. P(A wins) = sigmoid(beta * (sum skill_A - sum skill_B) + early-game noise).

    Built-in realism you should discover, not be told about:
    players join over time (cold start), skill drifts (non-stationarity),
    a few late-joining high-skill accounts (smurfs), imperfect skill-based lobbies.
    """
    skill0 = rng.normal(0.0, 1.0, n_players)
    join = rng.integers(0, int(0.7 * n_matches), n_players)
    join[: team_size * 40] = 0  # founding population

    smurf = np.zeros(n_players, bool)
    late = np.flatnonzero(join > 0.3 * n_matches)
    smurf[rng.choice(late, int(smurf_frac * n_players), replace=False)] = True
    skill0[smurf] = rng.normal(2.2, 0.3, smurf.sum())
    drift = rng.normal(0.0, 0.4, n_players)  # total change over the season

    order = np.argsort(join, kind="stable")
    join_sorted = join[order]

    rows = []
    for m in range(n_matches):
        active = order[: np.searchsorted(join_sorted, m, side="right")]
        cand = rng.choice(active, size=min(30, active.size), replace=False)
        cur = skill0[cand] + drift[cand] * np.clip((m - join[cand]) / n_matches, 0, 1)
        noisy = cur + rng.normal(0, mm_noise, cand.size)
        lobby_idx = np.argsort(np.abs(noisy - noisy[0]))[: 2 * team_size]
        lobby = rng.permutation(cand[lobby_idx])
        a, b = lobby[:team_size], lobby[team_size:]

        def s(ids):
            return (skill0[ids] + drift[ids] * np.clip((m - join[ids]) / n_matches, 0, 1)).sum()

        early = beta * (s(a) - s(b)) + rng.normal(0, 1.0)
        a_win = rng.random() < _sigmoid(0.9 * early)
        gold10 = int(round(800 * early + rng.normal(0, 300)))
        duration = float(np.clip(rng.normal(31 - 2.0 * abs(early), 5), 15, 55))
        rows.append((m, round(90 * m / n_matches, 3), *a, *b, gold10, round(duration, 1), int(a_win)))

    cols = (["match_id", "day"] + [f"a{i}" for i in range(1, team_size + 1)]
            + [f"b{i}" for i in range(1, team_size + 1)]
            + ["a_gold_diff_10", "duration_min", "a_win"])
    matches = pd.DataFrame(rows, columns=cols)
    truth = pd.DataFrame({
        "player_id": np.arange(n_players), "skill_at_join": skill0,
        "skill_end": skill0 + drift * np.clip((n_matches - join) / n_matches, 0, 1),
        "join_match": join, "is_smurf": smurf,
    })
    meta = pd.DataFrame({"param": ["beta", "early_to_win_scale", "mm_noise"],
                         "value": [beta, 0.9, mm_noise]})
    return {"matches.csv": matches}, {"players_truth.csv": truth, "params.csv": meta}


# ----------------------------------------------------------------------- newplayer
def sim_newplayer(rng, n_players=6000, days=28):
    """New-player activity. Churn is an absorbing event driven by a daily hazard.

    Planted structure: loss streaks, toxic-chat exposure and tenure affect the hazard;
    playing with friends protects; skill confounds (low skill -> more losses AND higher hazard);
    zero-game days happen without churning (inactivity != churn).
    """
    region = rng.choice(["NA", "EUW", "KR", "BR"], n_players, p=[.35, .35, .15, .15])
    source = rng.choice(["organic", "paid_ads", "friend_referral"], n_players, p=[.5, .3, .2])
    skill = rng.normal(0, 1, n_players)
    party_prone = rng.random(n_players) < np.where(source == "friend_referral", 0.7, 0.2)
    coef = dict(intercept=-3.4, loss_streak=0.30, toxic_today=0.6, party=-0.9,
                skill=-0.25, tenure_day=-0.04, paid_ads=0.4)

    events, churn_day = [], np.full(n_players, np.nan)
    for i in range(n_players):
        streak = 0
        for d in range(days):
            toxic_today = 0
            if rng.random() < 0.15:  # took a day off
                n_games = 0
            else:
                n_games = rng.poisson(2.2 + 1.2 * party_prone[i])
            for g in range(n_games):
                party = int(party_prone[i] and rng.random() < 0.6)
                win = int(rng.random() < _sigmoid(0.7 * skill[i] + 0.2 * party))
                toxic = int(rng.random() < 0.08 + 0.10 * (1 - win))
                toxic_today |= toxic
                kills = rng.poisson(4 + 2 * win + skill[i].clip(-1, 2))
                deaths = rng.poisson(6 - 2 * win)
                minutes = round(float(np.clip(rng.normal(30, 6), 15, 50)), 1)
                events.append((i, d, g, win, kills, deaths, minutes, party, toxic))
                streak = 0 if win else streak + 1
            logit = (coef["intercept"] + coef["loss_streak"] * streak
                     + coef["toxic_today"] * toxic_today + coef["party"] * party_prone[i]
                     + coef["skill"] * skill[i] + coef["tenure_day"] * d
                     + coef["paid_ads"] * (source[i] == "paid_ads"))
            if rng.random() < _sigmoid(logit):
                churn_day[i] = d
                break

    ev = pd.DataFrame(events, columns=["player_id", "day", "game_idx", "win", "kills",
                                       "deaths", "minutes", "in_party", "saw_toxic_chat"])
    players = pd.DataFrame({"player_id": np.arange(n_players), "region": region,
                            "signup_source": source})
    truth = pd.DataFrame({"player_id": np.arange(n_players), "skill": skill,
                          "party_prone": party_prone, "churn_day": churn_day})
    params = pd.DataFrame({"param": list(coef), "value": list(coef.values())})
    return ({"events.csv": ev, "players.csv": players},
            {"players_truth.csv": truth, "hazard_coefficients.csv": params})


# ---------------------------------------------------------------------------- shop
def sim_shop(rng, n_players=4000, n_items=400, n_champs=80, dim=8, days=90):
    """Skin purchases. Taste = latent factors shared between champion play and skin purchase.

    Planted structure: skins inherit their champion's embedding (champion play is useful
    side info), popularity/quality bias, price sensitivity, items release over time,
    you can't buy what you own, ~30% of players never buy (cold start).
    """
    C = rng.normal(0, 1, (n_champs, dim))
    U = rng.normal(0, 1, (n_players, dim))
    champ_pop = rng.normal(0, 0.7, n_champs)

    plays = []
    for i in range(n_players):
        p = _softmax(2.0 * U[i] @ C.T / np.sqrt(dim) + champ_pop)
        counts = rng.multinomial(rng.poisson(60) + 5, p)
        plays += [(i, c, int(n)) for c, n in enumerate(counts) if n > 0]

    item_champ = rng.integers(0, n_champs, n_items)
    V = C[item_champ] + rng.normal(0, 0.5, (n_items, dim))
    quality = rng.normal(0, 0.7, n_items)
    tier = rng.choice([1, 2, 3, 4], n_items, p=[.4, .3, .2, .1])
    release = np.where(rng.random(n_items) < 0.6, 0, rng.integers(1, days - 10, n_items))

    buys = []
    for i in range(n_players):
        if rng.random() < 0.30:
            continue
        owned = np.zeros(n_items, bool)
        for day in np.sort(rng.integers(0, days, rng.poisson(5) + 1)):
            avail = (release <= day) & ~owned
            if not avail.any():
                break
            logits = 2.0 * U[i] @ V[avail].T / np.sqrt(dim) + quality[avail] - 0.3 * tier[avail]
            j = np.flatnonzero(avail)[rng.choice(avail.sum(), p=_softmax(logits))]
            owned[j] = True
            buys.append((i, int(j), int(day)))

    purchases = pd.DataFrame(buys, columns=["player_id", "item_id", "day"])
    champ_play = pd.DataFrame(plays, columns=["player_id", "champion_id", "games"])
    items = pd.DataFrame({"item_id": np.arange(n_items), "champion_id": item_champ,
                          "price_tier": tier, "release_day": release})
    impressions, sf_params = _storefront_log(rng, purchases, U, V, quality, tier, release, days)
    return ({"purchases.csv": purchases, "champion_play.csv": champ_play, "items.csv": items,
             "impressions.csv": impressions},
            {"latent_factors.npz": dict(U=U, V=V, C=C, quality=quality),
             "storefront_params.csv": sf_params})


def _storefront_log(rng, purchases, U, V, quality, tier, release, days,
                    n_sessions=40_000, explore_frac=0.15):
    """Personalized-store impression log: 6 slots per session, position-biased clicks.

    Two traffic buckets: `prod` ranks by recent global popularity (not personalized, and
    no randomization), `explore` shows 6 random eligible items in random order. Click =
    examined(position) AND attracted(player, item); purchase happens only after a click.
    The true examination curve and click/purchase model are in _truth/storefront_params.csv,
    so you can compute the exact expected purchases of any ranking you produce.
    """
    theta = np.array([0.95, 0.72, 0.55, 0.43, 0.34, 0.27])
    K, n_items, dim = theta.size, V.shape[0], V.shape[1]
    daily = np.zeros((days, n_items))
    np.add.at(daily, (purchases.day.values, purchases.item_id.values), 1)
    cum_pop = np.cumsum(daily, axis=0)
    by_player = {pid: (g.item_id.values, g.day.values) for pid, g in purchases.groupby("player_id")}
    empty = (np.empty(0, int), np.empty(0, int))

    s_player = rng.integers(0, U.shape[0], n_sessions)
    s_day = np.sort(rng.integers(1, days, n_sessions))
    explore = rng.random(n_sessions) < explore_frac
    store_buys, rows = {}, []
    for s in range(n_sessions):
        i, d = int(s_player[s]), int(s_day[s])
        avail = release <= d
        it, dy = by_player.get(i, empty)
        avail[it[dy < d]] = False
        if i in store_buys:
            avail[store_buys[i]] = False
        cand = np.flatnonzero(avail)
        if cand.size < K:
            continue
        if explore[s]:
            shown = rng.choice(cand, K, replace=False)
        else:
            score = np.log1p(cum_pop[d - 1, cand]) + rng.normal(0, 0.3, cand.size)
            shown = cand[np.argsort(-score)[:K]]
        aff = U[i] @ V[shown].T / np.sqrt(dim)
        attract = _sigmoid(1.0 * aff + quality[shown] - 0.25 * tier[shown] - 3.0)
        click = rng.random(K) < theta * attract
        buy = click & (rng.random(K) < _sigmoid(0.8 * aff - 0.3 * tier[shown] - 1.2))
        if buy.any():
            store_buys.setdefault(i, []).extend(shown[buy].tolist())
        bucket = "explore" if explore[s] else "prod"
        for k in range(K):
            rows.append((s, i, d, bucket, k + 1, int(shown[k]), int(click[k]), int(buy[k])))

    imp = pd.DataFrame(rows, columns=["session_id", "player_id", "day", "bucket", "position",
                                      "item_id", "clicked", "purchased"])
    params = pd.DataFrame({
        "param": [f"examine_pos{k + 1}" for k in range(K)] + [
            "attract = sigmoid(a_aff*aff + quality - a_tier*tier + a0), aff = U@V/sqrt(dim)",
            "a_aff", "a_tier", "a0",
            "p_buy_given_click = sigmoid(b_aff*aff - b_tier*tier + b0)",
            "b_aff", "b_tier", "b0"],
        "value": list(theta) + [np.nan, 1.0, 0.25, -3.0, np.nan, 0.8, 0.3, -1.2],
    })
    return imp, params


# ----------------------------------------------------------------------- lifecycle
PRICE_POINTS = np.array([4.99, 9.99, 19.99, 34.99, 49.99, 99.99])
ITEM_TYPES = np.array(["chroma", "skin", "skin", "bundle", "bundle", "prestige"])


def _run_world(lat, treat, days, cutoff, offer_days, event, seed):
    """One simulated world. Random draws depend only on (seed, day), never on state, so two
    worlds that differ only in `treat` share every random number -> exact counterfactuals."""
    n = lat["engage"].size
    state = np.zeros(n, np.int8)            # 0 not signed up, 1 active, 2 lapsed, 3 churned
    payer = lat["payer0"].copy()
    streak = np.zeros(n)
    lapsed_for = np.zeros(n)
    act_rows, buy_rows, snap = [], [], None
    pos = np.arange(6)[None, :]
    for d in range(days):
        g = np.random.default_rng([seed, d])
        u = g.random((n, 7))
        z = g.standard_normal((n, 2))
        ug = g.random((n, 6))
        up = g.random((n, 6))
        state[lat["signup"] == d] = 1
        if d == cutoff:
            snap = dict(state=state.copy(), lapsed_for=lapsed_for.copy(), payer=payer.copy())
        in_offer = treat & (d >= cutoff) & (d < cutoff + offer_days)
        post_offer = treat & (d >= cutoff + offer_days) & (d < cutoff + 2 * offer_days)

        act = state == 1
        lap = state == 2
        play = act & (u[:, 0] < lat["engage"])
        k = 1 + np.floor(np.log(u[:, 1]) / np.log(0.55)).astype(int)
        games = np.where(play, np.minimum(k, 6), 0)
        valid = pos < games[:, None]
        won = (ug < 0.5) & valid
        wins = won.sum(1)
        party = ((up < np.where(lat["social"], 0.6, 0.1)[:, None]) & valid).sum(1)
        minutes = np.round(games * np.clip(28 + 6 * z[:, 0], 12, 50), 1)

        # trailing loss streak within the day
        trail = np.zeros(n)
        alive = np.ones(n, bool)
        for j in range(5, -1, -1):
            v = valid[:, j] & alive
            lost_j = v & ~won[:, j]
            trail += lost_j
            alive &= ~(v & won[:, j])
        streak = np.where(play, np.where(wins == 0, streak + games, trail), streak)

        # monetization
        newly = play & ~payer & (u[:, 2] < np.where(in_offer, 0.004, 0.0003))
        payer |= newly
        mult = np.where(in_offer, 1.6, np.where(post_offer, 0.8, 1.0))
        buy = (play & payer & (u[:, 3] < lat["spend_rate"] * mult)) | newly
        tier = np.clip(np.round(lat["amount_mu"] + 0.8 * z[:, 1]), 0, 5).astype(int)
        price = np.round(PRICE_POINTS[tier] * np.where(in_offer, 0.5, 1.0), 2)

        idx = np.flatnonzero(play)
        act_rows.append(np.column_stack([idx, np.full(idx.size, d), games[idx], wins[idx],
                                         party[idx], minutes[idx]]))
        b = np.flatnonzero(buy)
        buy_rows.append((b, np.full(b.size, d), price[b], tier[b], in_offer[b]))

        # lifecycle transitions
        tenure = d - lat["signup"]
        ev = event[d]
        lapse_logit = (-4.0 + 0.20 * np.minimum(streak, 8) - 0.8 * lat["social"]
                       + 1.3 * np.exp(-np.maximum(tenure, 0) / 14) - 0.8 * ev
                       - 2.0 * (lat["engage"] - 0.67))
        boost = np.where(in_offer, 0.4 + 0.9 * lat["social"] + 0.8 * (lapsed_for < 30), 0.0)
        revive_logit = (-4.1 + 1.8 * ev + 0.7 * lat["social"]
                        - 0.03 * np.minimum(lapsed_for, 120) + boost)
        to_lapse = act & (u[:, 4] < _sigmoid(lapse_logit))
        to_active = lap & (u[:, 5] < _sigmoid(revive_logit))
        to_churn = lap & ~to_active & (u[:, 6] < 0.008 + 0.02 * (lapsed_for > 60))
        state[to_lapse] = 2
        state[to_active] = 1
        state[to_churn] = 3
        lapsed_for = np.where(state == 2, lapsed_for + 1, 0)
        streak[to_lapse | to_active] = 0

    act = np.vstack(act_rows)
    b_idx, b_day, b_price, b_tier, b_offer = (np.concatenate(x) for x in zip(*buy_rows))
    return act, (b_idx, b_day, b_price, b_tier, b_offer), snap


def sim_lifecycle(rng, n_players=12000, days=270, cutoff=180, offer_days=30, exp_frac=0.3):
    """Established + new players over 270 days: activity, purchases, and a randomized
    win-back / offer campaign sent on day `cutoff`.

    Planted structure (discover it, don't assume it): lapsed players can come back
    (revival), especially around content events; lapsed and truly churned players look
    identical in the logs; most players never pay and spend is heavy-tailed; the offer
    helps some segments, does nothing for others, and cannibalizes full-price spend
    for existing payers. The answer key holds exact potential outcomes for every
    experiment player, so you can score an uplift model against the true effect.
    """
    n = n_players
    signup = np.where(rng.random(n) < 0.4, 0, rng.integers(1, cutoff, n))
    source = rng.choice(["organic", "paid_ads", "friend_referral"], n, p=[.5, .3, .2])
    lat = dict(
        signup=signup,
        social=rng.random(n) < np.where(source == "friend_referral", 0.6, 0.25),
        engage=rng.beta(4, 2, n),
        spend_rate=rng.gamma(2.0, 0.03, n),
        amount_mu=rng.normal(1.2, 0.9, n),
    )
    lat["payer0"] = rng.random(n) < 0.10 + 0.06 * lat["social"]
    in_exp = (signup <= cutoff - 30) & (rng.random(n) < exp_frac)
    treated = in_exp & (rng.random(n) < 0.5)
    event = np.zeros(days, bool)
    event_starts = list(range(30, days, 45))
    for e in event_starts:
        event[e:e + 7] = True

    seed = int(rng.integers(2**62))
    act0, buy0, snap0 = _run_world(lat, np.zeros(n, bool), days, cutoff, offer_days, event, seed)
    act1, buy1, _ = _run_world(lat, in_exp, days, cutoff, offer_days, event, seed)

    # observed world: treated players live in world 1, everyone else in world 0
    keep0, keep1 = ~treated[act0[:, 0].astype(int)], treated[act1[:, 0].astype(int)]
    act = np.vstack([act0[keep0], act1[keep1]])
    activity = pd.DataFrame(act, columns=["player_id", "day", "games", "wins",
                                          "party_games", "minutes"])
    activity = activity.astype({c: int for c in ["player_id", "day", "games", "wins", "party_games"]})
    activity = activity.sort_values(["day", "player_id"]).reset_index(drop=True)

    def buys_df(bb, mask_fn):
        i, d, p, t, o = bb
        m = mask_fn(i)
        return pd.DataFrame({"player_id": i[m], "day": d[m], "amount_usd": p[m],
                             "item_type": ITEM_TYPES[t[m]], "offer_price": o[m]})
    purchases = pd.concat([buys_df(buy0, lambda i: ~treated[i]), buys_df(buy1, lambda i: treated[i])])
    purchases = purchases.sort_values(["day", "player_id"]).reset_index(drop=True)

    players = pd.DataFrame({
        "player_id": np.arange(n), "signup_day": signup,
        "region": rng.choice(["NA", "EUW", "KR", "BR", "LATAM"], n, p=[.3, .3, .15, .15, .1]),
        "platform": rng.choice(["pc", "mobile"], n, p=[.8, .2]),
        "acquisition_source": source,
    })
    ids = np.flatnonzero(in_exp)
    campaign = pd.DataFrame({"player_id": ids, "treated": treated[ids].astype(int),
                             "send_day": cutoff,
                             "offer": "50% off any item for 30 days + comeback reward"})
    calendar = pd.DataFrame({"start_day": event_starts,
                             "event": [f"content_event_{k}" for k in range(len(event_starts))]})

    # answer key
    def window_sum(a_or_b, world_is_buy, lo, hi, what):
        if world_is_buy:
            i, d, p, _, _ = a_or_b
            m = (d >= lo) & (d < hi)
            return np.bincount(i[m], weights=p[m], minlength=n)
        m = (a_or_b[:, 1] >= lo) & (a_or_b[:, 1] < hi)
        return np.bincount(a_or_b[m, 0].astype(int), minlength=n)

    po = pd.DataFrame({
        "player_id": ids,
        "revenue_90d_control": window_sum(buy0, True, cutoff, cutoff + 90, None)[ids].round(2),
        "revenue_90d_treated": window_sum(buy1, True, cutoff, cutoff + 90, None)[ids].round(2),
        "active_days_30d_control": window_sum(act0, False, cutoff, cutoff + 30, None)[ids],
        "active_days_30d_treated": window_sum(act1, False, cutoff, cutoff + 30, None)[ids],
        "active_days_90d_control": window_sum(act0, False, cutoff, cutoff + 90, None)[ids],
        "active_days_90d_treated": window_sum(act1, False, cutoff, cutoff + 90, None)[ids],
    })
    state_names = np.array(["not_signed_up", "active", "lapsed", "churned"])
    truth = pd.DataFrame({
        "player_id": np.arange(n), "social": lat["social"], "engage": lat["engage"].round(3),
        "payer_initial": lat["payer0"], "payer_at_cutoff": snap0["payer"],
        "spend_rate": lat["spend_rate"].round(4), "amount_mu": lat["amount_mu"].round(3),
        "state_at_cutoff": state_names[snap0["state"]],
        "days_lapsed_at_cutoff": snap0["lapsed_for"].astype(int),
    })
    params = pd.DataFrame({"param": ["cutoff_day", "offer_days", "offer_discount",
                                     "offer_buy_rate_mult", "post_offer_buy_rate_mult"],
                           "value": [cutoff, offer_days, 0.5, 1.6, 0.8]})
    return ({"players.csv": players, "activity.csv": activity, "purchases.csv": purchases,
             "campaign.csv": campaign, "content_calendar.csv": calendar},
            {"players_truth.csv": truth, "potential_outcomes.csv": po, "params.csv": params})


# ---------------------------------------------------------------------------- main
def _write(folder: Path, public: dict, truth: dict):
    (folder / "_truth").mkdir(parents=True, exist_ok=True)
    for name, df in public.items():
        df.to_csv(folder / name, index=False)
    for name, obj in truth.items():
        path = folder / "_truth" / name
        if name.endswith(".npz"):
            np.savez(path, **obj)
        else:
            obj.to_csv(path, index=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="data/sim")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--only", choices=["lifecycle", "shop", "newplayer", "ranked"])
    args = ap.parse_args()
    out = Path(args.out)
    sims = {"lifecycle": sim_lifecycle, "shop": sim_shop,
            "newplayer": sim_newplayer, "ranked": sim_ranked}
    for name, fn in sims.items():
        if args.only and name != args.only:
            continue
        rng = np.random.default_rng([args.seed, list(sims).index(name)])
        public, truth = fn(rng)
        _write(out / name, public, truth)
        sizes = ", ".join(f"{k}: {len(v):,} rows" for k, v in public.items())
        print(f"[{name}] {sizes}")


if __name__ == "__main__":
    main()
