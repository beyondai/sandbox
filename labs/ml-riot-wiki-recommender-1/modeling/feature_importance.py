"""Quick importance check for the feature list (train split only).

Holds out 10% of the train queries, fits a small HistGradientBoosting
regressor on log1p(r), and measures permutation importance as the drop in
nDCG@5 on the held-out queries, overall and on the new and long_tail query
slices. Also fits once without each feature group (group ablation).
Never reads the test split.

Run: uv run python3 modeling/feature_importance.py   (from the project folder)
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingRegressor

from features import FEATURES

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[2] / "data" / "wikipedia-clickstream" / "modeling"
SEED, K = 42, 5
GROUPS = {
    "opened_next": ["log_n_ac", "p_c_given_a", "rank_ac", "is_link_ac"],
    "reverse": ["log_n_ca", "p_a_given_c"],
    "twohop": ["twohop", "twohop_paths"],
    "item": ["log_in_c", "log_out_c", "log_views_c", "log_in_c_per_day", "item_age_days", "item_is_new"],
    "query": ["log_out_a", "log_views_a", "q_age_days", "q_is_new"],
    "cand_flags": ["cand_opened_next", "cand_twohop", "cand_reverse", "cand_popular", "n_sources"],
}


def ndcg_at_k(df: pl.DataFrame, score: np.ndarray) -> pl.DataFrame:
    """Per-query nDCG@K over the candidates, gain = label (log1p r).
    The ideal uses candidates only; candidate recall is reported separately."""
    d = df.select("q", "q_slice", "label").with_columns(s=pl.Series(score))
    top = d.sort(["q", "s"], descending=[False, True]).group_by("q", maintain_order=True).head(K)
    ideal = d.sort(["q", "label"], descending=[False, True]).group_by("q", maintain_order=True).head(K)
    disc = 1.0 / (pl.int_range(pl.len()).over("q") + 2).cast(pl.Float64).log(2)
    dcg = top.with_columns(g=pl.col("label") * disc).group_by("q").agg(dcg=pl.col("g").sum())
    idcg = ideal.with_columns(g=pl.col("label") * disc).group_by("q").agg(
        idcg=pl.col("g").sum(), q_slice=pl.col("q_slice").first()
    )
    return idcg.join(dcg, on="q").with_columns(
        ndcg=pl.when(pl.col("idcg") > 0).then(pl.col("dcg") / pl.col("idcg")).otherwise(0.0)
    )


def summary(per_q: pl.DataFrame) -> dict:
    out = {"all": per_q["ndcg"].mean()}
    for s in ("new", "long_tail"):
        out[s] = per_q.filter(pl.col("q_slice") == s)["ndcg"].mean()
    return out


def fit(X: np.ndarray, y: np.ndarray) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        max_iter=200, learning_rate=0.1, max_leaf_nodes=31, min_samples_leaf=100, random_state=SEED
    ).fit(X, y)


def main() -> None:
    df = pl.read_parquet(OUT / "features_train.parquet")
    qs = df.select("q").unique().sort("q")
    rng = np.random.default_rng(SEED)
    hold = qs.filter(pl.Series(rng.random(qs.height) < 0.10))
    tr = df.join(hold, on="q", how="anti").sample(fraction=0.5, seed=SEED)
    ho = df.join(hold, on="q", how="semi").sort(["q", "item"])
    y = tr["label"].to_numpy()
    Xh = ho.select(FEATURES).to_numpy().astype(float)

    model = fit(tr.select(FEATURES).to_numpy().astype(float), y)
    base = summary(ndcg_at_k(ho, model.predict(Xh)))
    print("base nDCG@5", {k: round(v, 4) for k, v in base.items()}, flush=True)

    perm = {}
    for j, f in enumerate(FEATURES):
        Xp = Xh.copy()
        Xp[:, j] = rng.permutation(Xp[:, j])
        s = summary(ndcg_at_k(ho, model.predict(Xp)))
        perm[f] = {k: round(base[k] - s[k], 4) for k in base}
        print("perm", f, perm[f], flush=True)

    ablate = {}
    for g, cols in GROUPS.items():
        keep = [f for f in FEATURES if f not in cols]
        m = fit(tr.select(keep).to_numpy().astype(float), y)
        s = summary(ndcg_at_k(ho, m.predict(ho.select(keep).to_numpy().astype(float))))
        ablate[g] = {k: round(base[k] - s[k], 4) for k in base}
        print("drop group", g, ablate[g], flush=True)

    res = {
        "holdout_queries": hold.height, "fit_rows": tr.height, "holdout_rows": ho.height,
        "base_ndcg5": {k: round(v, 4) for k, v in base.items()},
        "permutation_drop": perm, "group_ablation_drop": ablate,
    }
    (HERE / "feature_importance.json").write_text(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
