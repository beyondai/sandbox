# KKBOX Recommendation - Post-Delivery (Quick POC)

Quick POC mode: each item states its most likely answer in one pass,
flagged as an assumption where noted. Since `prd/kkbox-recommendation.md`
scoped real deployment out of this exercise, Analysis and Iteration below
build on `modeling/04-evaluate.md`'s real offline results and
`design/delivery.md`'s hypothetical rollout plan, not an actual A/B
outcome.

## Analysis

*(post-A/B deep-dive plan, hypothetical - no real A/B ran per
`design/delivery.md`)* If the hypothetical shadow/ramp in
`design/delivery.md` ran and moved (or didn't move) repeat-listen rate,
the deep-dive would segment by:

- **Listening context** (`source_system_tab`/`source_screen_name`/
  `source_type`) - the single dominant signal group throughout this
  project (see Explainability below); if the online lift is concentrated
  in one context (e.g. "my library" sessions) and flat elsewhere, that
  says the model is really a library-replay detector more than a general
  recommender, and scopes what V2 should actually target.
- **Entity exposure** (`msno_count`/`song_count`/`artist_count` - how
  much history backed each row's smoothed repeat-rate): rows with high
  exposure (well-established users/songs/artists) vs. low exposure
  (near-`global_mean`, effectively cold-start) should be analyzed
  separately - a lift concentrated in the high-exposure segment would
  mean this model isn't actually solving the cold-start problem the PRD
  explicitly said it wasn't targeting, confirming scope was set
  correctly rather than accidentally.
- **Membership tenure** (`membership_duration_days`): whether the model
  helps newer vs. longer-tenured members differently.

## Explainability

**Real global importances**, computed from the actual trained model
(`modeling/train-candidates/random-forest/model.joblib`), not estimated:

| Feature | Importance |
|---|---|
| `msno_repeat_rate_loo` | 0.2476 |
| `source_context_freq` | 0.0901 |
| `source_system_tab_my library` | 0.0746 |
| `song_count` | 0.0728 |
| `song_repeat_rate_loo` | 0.0676 |
| `source_screen_name_Local playlist more` | 0.0611 |
| `artist_repeat_rate_loo` | 0.0598 |

A single feature - **the user's own historical repeat-listen rate** -
carries roughly a quarter of total importance, more than double the next
feature. This is a real, evidence-backed answer to "why does this model
work": it's mostly learning "does this user tend to replay songs at
all," with listening context as the second-strongest signal group and
song/artist-level history a clear third. This also retroactively
validates the effort spent fixing the CV-leakage bug in
`modeling/03-train.md` - the feature that mattered most for the fix
(`msno_repeat_rate_loo`) is also the feature that matters most for the
model's actual predictions.

- **Global**: the table above (`feature_importances_` from the trained
  `RandomForestClassifier`) - already computed, not hypothetical.
- **Local (per-prediction)**: not computed for this POC. SHAP's
  `TreeExplainer` is the natural fit for a Random Forest (exact, not
  approximated, for tree ensembles) and would be the right next step for
  debugging individual predictions or stakeholder-facing "why was this
  song recommended to this user" explanations - reasonable next-iteration
  work, not done here.

## Iteration

Concrete next-version items, grounded in this project's own findings
(not "TBD based on results"):

- **V1** (per `design/high-level.md`'s Phasing, refined by what this POC
  learned): train on the full `train.csv` instead of the ~8.1% sample
  used throughout this project (`01-data.md`) - `msno_repeat_rate_loo`
  dominating importance suggests more historical exposure per entity
  could meaningfully improve the aggregate features' quality, not just
  add rows.
- **Revisit gradient boosting properly**: `HistGradientBoostingClassifier`
  underperformed badly in both the original comparison and a tuned
  autoresearch retry (`modeling/03-train.md`,
  `modeling/autoresearch/rounds/round-0001/`) - a genuine LightGBM/XGBoost
  attempt (blocked in this session by a missing system `libomp` library,
  not a modeling problem) is worth retrying once that's resolved, since
  neither this project nor `monkey-mode/report.md` has actually validated
  gradient boosting works here, only that scikit-learn's specific
  implementation didn't with default-ish settings.
- **Tune the smoothing constant**: `SMOOTHING_K = 10` in
  `build_features.py` was a convention pulled from the newly-documented
  `ml-modeling-features/SKILL.md` technique, never itself searched -
  worth a small sweep given how much weight `msno_repeat_rate_loo`
  carries.
- **Multi-valued genre**: `02-features.md` deliberately kept only the
  primary genre id, dropping secondary genres as a POC simplification -
  worth revisiting given genre never surfaced as a top feature either way
  (weak evidence it doesn't matter, but not a real test of the
  multi-hot alternative).
- **V2** (per `design/high-level.md`): sequential/two-tower modeling and
  the online A/B infrastructure in `design/delivery.md`, once V1's
  full-dataset retrain is validated.
- **Real leaderboard check** (deferred, see the saved memory note): a
  genuine Kaggle submission would validate this model against the wider
  community benchmark, with the caveat that even a real submission stays
  an unequal comparison (full dataset + `user_logs.csv` vs. this
  project's smaller scope) - see `04-evaluate.md`'s comparability note.

## Democratize

Named components, named (hypothetical, per PRD's Team - Reuse)
consumers - not "this could help others" in the abstract:

- **Personalization/Recommendation team** (`prd/kkbox-recommendation.md`'s
  hypothetical stakeholder): the leave-one-out, count-weighted-smoothed
  entity-aggregate pattern in `build_features.py` (`SMOOTHING_K = 10`,
  `(others_sum + k*global_mean) / (others_count + k)`) generalizes to any
  per-user/per-item historical-rate feature, not just repeat-listen -
  directly reusable for adjacent prediction tasks this team would
  plausibly own, like skip prediction or session-length prediction.
- **Data engineering team** (same PRD section): `build_test_features.py`'s
  pattern - recompute deterministic features directly, left-join
  target-derived aggregates from train-only lookup tables, align one-hot
  columns exactly, explicit fallback for unseen keys - is a reusable
  template for productionizing *any* feature pipeline built on target
  encoding, since the train/score leakage problem it solves recurs
  everywhere target encoding is used, not just here.
- **Already happened, not hypothetical**: the fold-safe CV methodology
  fix and the dashboard `Model Comparison` bug fix from this project were
  fed back as real edits to the shared `ml-modeling-features`/
  `ml-modeling-train`/`ml-modeling-multiagent` skill files and the shared
  `dashboard_app.py` template (see `SKILL-IMPROVEMENTS.md`) - every
  future `ml-modeling-*` practice project already inherits both fixes
  automatically. This is the closest thing this solo practice project has
  to a real cross-team reuse story, and it's concrete: two specific bugs,
  fixed once, reused by every project that comes after.

## Change log

- 2026-09-21: initial Post-Delivery section for the Quick POC.
