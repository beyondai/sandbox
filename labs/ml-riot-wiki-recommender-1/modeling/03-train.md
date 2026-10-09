# 03 - Train

- Mode: Quick POC (the chain's mode), 2026-10-09.
- Design docs: the spec hashes match the current PRD and
  `design/high-level.md`.
- Code: `modeling/train.py`. Results: `modeling/train_results.json`,
  `modeling/experiments.json` (6 runs), `modeling/train.log`.
- Proxy rule: as in `01-data.md`. **For Riot** lines are the design input.

## Selected model

**`hgb_log1p`**: scikit-learn `HistGradientBoostingRegressor`, squared
error on `log1p(r)`, the 23 features of `02-features.md`. Saved to
`modeling/model.joblib` (fit on all 6,185,251 train rows).

- It is the design's V1 model class (GBDT, graded label) and the label
  sweep's default. No other label beat it (see "Label sweep").
- It beats the V0 rule and the simplest learned model (ridge), but by
  small margins, and it is slightly worse than V0 on head pages. On the
  proxy, it does **not** pass the complexity gate on the new slice (see
  "Complexity gate").

## Candidates and setup

```
v0_rule          no fit: opened-next count, then reverse count, then views
ridge_log1p      StandardScaler + Ridge(alpha=1), nulls -> 0 + missing flags
hgb_log1p        GBDT, squared error, target log1p(r)          (default)
hgb_poisson_raw  GBDT, Poisson loss, target r                  (sweep)
hgb_sqrt         GBDT, squared error, target sqrt(r)           (sweep)
hgb_share        GBDT, squared error, target r / R(A)          (sweep)
```

- **Architecture.** Shallow: a GBDT on tabular pair features (the
  reference's "ranking with rich features" row). No DNN: about 6M rows of
  dense numeric features, no ids or sequences, and GBDT is the standard
  winner on this shape. A DNN ranker (MLP or DCN-v2) is a later option
  only if text embeddings enter as raw vectors, not as cosine features.
- **Loss.** Pointwise regression on the graded label, so the model
  predicts expected opened-next readers (log scale) and ranks by it.
- **Negatives.** As in `01-data.md`: hard negatives from the candidate
  rules (label 0), no sampling, no correction.
- **GBDT hyperparameters** (POC sizes):
  - `max_iter` 100 (trees), `learning_rate` 0.1, `max_leaf_nodes` 31,
    `min_samples_leaf` 100, `l2_regularization` 0;
  - no early stopping (fixed size, so folds compare);
  - nulls handled natively (`rank_ac`, `is_link_ac`, the age features).
- **Ridge.** `alpha` 1.0, standardized inputs, a missing flag for each
  nullable feature.
- **CV.** 3 folds, `GroupKFold` by query, so no query is in both the fit
  and the scored fold. The CV uses **50% of the train queries (58,533
  queries, 3,080,222 rows, 49.8% of the train table)** to fit the time
  budget. Regular mode: 5 folds, 200 trees, all queries.
- **Metrics** (out-of-fold, per query):
  - nDCG@5, gain `log1p(r)` for every candidate, so all labels are scored
    on the same scale. The ideal ranking uses the candidates only, so this
    measures ranking, not candidate recall.
  - `recall_w@5`: clicks on the top 5 / all label-month clicks from A
    (`truth_train`), so it includes the candidate-recall ceiling.
  - "Weighted" = the mean over slices, weighted by each slice's share of
    the source-page population (long_tail 50.7%, torso 38.6%, head 9.8%,
    dormant 0.5%, new 0.4%).
  - 95% CIs: paired bootstrap over queries within each slice, 1,000
    draws.
- **Threshold.** None: the output is a ranking, and the panel shows the
  top 5. `model.joblib` stores `threshold: None`.
- **CV leak check.** No feature uses the label (`02-features.md`), so no
  per-fold recomputation is needed. The CV ranking is not provisional.
- **Hardware and time.** Intel i7-10700K, 16 threads, CPU only. CV time
  per candidate: rule 1 s, ridge 5 s, GBDT 12-18 s (3 folds). Final fit
  on 6.2M rows: 14 s. Whole run: 89 s. Tuning budget: none (one fixed
  setting per candidate).

## Results (out-of-fold, train CV)

nDCG@5 (weighted, then new / dormant / long_tail / torso / head):

- `v0_rule`: 0.8597; 0.421 / 0.131 / 0.768 / 0.961 / 0.992.
- `ridge_log1p`: 0.8623; 0.423 / 0.131 / 0.773 / 0.962 / 0.992.
- **`hgb_log1p`: 0.8635; 0.423 / 0.131 / 0.775 / 0.962 / 0.990.**
- `hgb_sqrt`: 0.8630; 0.424 / 0.130 / 0.774 / 0.962 / 0.990.
- `hgb_share`: 0.8632; 0.424 / 0.130 / 0.774 / 0.962 / 0.992.
- `hgb_poisson_raw`: 0.5472; 0.246 / 0.038 / 0.290 / 0.787 / 0.974.

`recall_w@5` (weighted): V0 0.7184, ridge 0.7206, `hgb_log1p` 0.7212,
sqrt 0.7210, share 0.7214, Poisson 0.4373. By slice for `hgb_log1p`: new
0.329, dormant 0.127, long_tail 0.729, torso 0.770, head 0.537.

### Deltas with 95% CIs (nDCG@5)

`hgb_log1p` - `v0_rule`:

- weighted +0.0038 [+0.0033, +0.0043];
- long_tail +0.0066 [+0.0057, +0.0074];
- torso +0.0015 [+0.0011, +0.0020];
- new +0.0014 [-0.0004, +0.0032] (not significant);
- dormant -0.0002 [-0.0011, +0.0006];
- head -0.0014 [-0.0019, -0.0009] (worse).

`hgb_log1p` - `ridge_log1p`: weighted +0.0012 [+0.0008, +0.0015];
long_tail +0.0020 [+0.0014, +0.0027]; head -0.0014 [-0.0018, -0.0010].

## Label sweep (design Open items)

Rule: a label replaces `log1p(r)` only if it wins on new and long_tail
with CIs above 0 and does not lose overall.

- `hgb_sqrt` - `hgb_log1p`: new +0.0010 [-0.0001, +0.0021], long_tail
  -0.0008 [-0.0012, -0.0003], weighted -0.0005. Fails.
- `hgb_share` - `hgb_log1p`: new +0.0015 [+0.0002, +0.0027], long_tail
  -0.0001 [-0.0007, +0.0004], weighted -0.0002 [-0.0006, +0.0001]. Fails
  on long_tail (no win). Closest challenger: better on new and head.
- `hgb_poisson_raw`: -0.316 weighted. Fails by far. With 100 trees at
  learning rate 0.1, the Poisson fit on counts up to 370k is dominated by
  the largest pairs and underfits the rest. This is untuned; it says raw
  counts need a much larger tuning budget, not that Poisson is wrong.
- LambdaMART on 0-4 grades: **not run**. LightGBM needs the system
  library `libomp`, which is not installed (a system install is the
  user's call). The package was removed again from the shared env.
- **Result: keep `log1p(r)`.**

## Complexity gate

The design gate for V1 (`design/high-level.md`): beat V0 on the new and
long_tail slices with CIs above 0, and not be worse overall.

- long_tail: passes (+0.0066, CI above 0).
- new: **fails** (+0.0014, CI includes 0).
- overall: passes (+0.0038). But head is worse (-0.0014).

Cost table, `hgb_log1p` against `v0_rule` and `ridge_log1p`:

- **Value of the gain.** About +0.4% nDCG@5 overall and +0.9% on
  long_tail pages over V0; +0.1% over ridge. Small on the proxy.
- **Running cost.** Nightly batch on CPU: about 15 s to fit 6M rows, and
  scoring 40k pages x 100 candidates is seconds. Same order as ridge.
- **Maintenance cost.** A weekly retrain and a model registry, which V0
  does not need. Ridge needs the same. No new data dependency.
- **Explainability.** Lower than V0 and ridge. Soft factor here (internal
  ranking, cheap errors); per-pair SHAP is available if needed.
- **Risk.** Low: GBDT is standard; V0 stays as the fallback.

Decision: the value is larger than the cost **only with the Riot
features**. On the proxy, the click features carry the same information
as the V0 rule, so the model can only re-weigh it. The design's reason for
V1 is the text, structure and age features (`02-features.md`), which the
proxy can't supply. So:

- Keep `hgb_log1p` as the V1 model class; the code accepts the extra
  columns (one list in `features.py`, nulls handled).
- Ship it behind the gate: on Riot data, V1 must pass the gate on new and
  long_tail with the structure and text features. If it does not, keep V0.
- Use the design's hybrid for head pages: V0 ranks head pages, the model
  ranks the rest. On the proxy, this removes the -0.0014 head loss.
- **For Riot:** expect the new-page gain to come from the new candidate
  sources and text features, not from this re-weighing of clicks.

## Training code (core, as run)

```python
HGB = dict(max_iter=100, learning_rate=0.1, max_leaf_nodes=31, min_samples_leaf=100,
           l2_regularization=0.0, early_stopping=False, random_state=SEED)

def fit_predict(cfg, tr, te):
    if cfg["kind"] == "rule":
        s = (te["log_n_ac"].exp() - 1) * 1e12 + (te["log_n_ca"].exp() - 1) * 1e6 + te["log_views_c"]
        return None, s.to_numpy()
    y = target(tr, cfg["target"])
    if cfg["kind"] == "ridge":
        m = make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(linear_matrix(tr), y)
        return m, m.predict(linear_matrix(te))
    m = HistGradientBoostingRegressor(loss=cfg["loss"], **HGB)
    m.fit(tr.select(FEATURES).to_numpy().astype(float), y)
    return m, m.predict(te.select(FEATURES).to_numpy().astype(float))

for name, cfg in CANDIDATES.items():
    oof = np.zeros(cv.height)
    for tr_i, te_i in GroupKFold(n_splits=3).split(cv, groups=cv["q"].to_numpy()):
        _, oof[te_i] = fit_predict(cfg, cv[tr_i], cv[te_i])
```

Full script: `modeling/train.py`. Out-of-fold scores per candidate:
`<sandbox>/data/wikipedia-clickstream/modeling/oof_<name>.parquet`
(git-ignored), so a metric change reruns only the metric code.

## Notes for the evaluate step

- Score `pairs_test` with `transform(pairs_test, "test")` and
  `model.joblib`; compare with `v0_rule` on the same candidates.
- Use the full truth (`truth_test`) for recall, so candidate misses count.
- Report the hybrid (V0 on head) next to the pure model.
- This CV's nDCG@5 uses the candidate-only ideal. It is higher than a
  truth-based nDCG@5, so don't compare it with monkey-mode numbers.
  Monkey mode's large cold-page gain (+0.26) was against a popularity-only
  fallback; here V0 already uses reverse counts, so it is much stronger.

## Change log

- 2026-10-09: created.
