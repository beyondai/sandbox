"""Serving function for the V1 ranker (the nightly batch job calls it).

score(df) takes candidate pair rows (the columns of dataset.test without
the label: q, item, cand_* flags, q_slice, item_slice) and returns one
score per row. Higher is better within a source page q; the job keeps the
top 20 per q for the key-value store.

- Features: transform() from features.py, the same code as training (no
  copied feature logic, so no training-serving skew).
- Model: model.joblib, loaded once at import.
- Routing (design gate, 03-train.md): the model ranks long_tail and torso
  source pages; the V0 rule ranks new, dormant and head pages. Each q is
  in one slice, so the two score scales never mix inside a ranking.
- History: the latest feature window. On the proxy that is the test
  split's window (August 2026); in Riot, the last 28 days.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import polars as pl

from features import transform

HERE = Path(__file__).resolve().parent
BUNDLE = joblib.load(HERE / "model.joblib")
MODEL_SLICES = ["long_tail", "torso"]
HISTORY = "test"
LABEL_COLS = ["r", "label"]


def score(df: pd.DataFrame | pl.DataFrame) -> np.ndarray:
    pairs = pl.from_pandas(df) if isinstance(df, pd.DataFrame) else df
    pairs = pairs.drop([c for c in LABEL_COLS if c in pairs.columns])
    feats = transform(pairs.with_row_index("_row"), HISTORY).sort("_row")
    model = BUNDLE["model"].predict(feats.select(BUNDLE["features"]).to_numpy().astype(float))
    v0 = ((feats["log_n_ac"].exp() - 1) * 1e12 + (feats["log_n_ca"].exp() - 1) * 1e6 + feats["log_views_c"]).to_numpy()
    use_model = feats["q_slice"].is_in(MODEL_SLICES).to_numpy()
    return np.where(use_model, model, v0)
