# 04 - Evaluate

- Mode: Quick POC (the chain's mode), 2026-10-09.
- Design docs: `design/high-level.md` changed in this session (the
  complexity gate became per-slice routing, a user decision). This chain
  made the change, so the spec hash was refreshed; no other change.
- Code: `modeling/evaluate.py`. Results: `modeling/evaluate_results.json`,
  `modeling/04-evaluate.json` (dashboard), `modeling/evaluate.log`.
  Per-row scores (git-ignored; parquet, not the skill's CSV, as in
  `01-data.md`):
  `<sandbox>/data/wikipedia-clickstream/modeling/test_scores.parquet`.
- **This is a backtest at a later cutoff, not a random hold-out:**
  features from August 2026, labels from September 2026, scored once.
- Proxy rule: as in `01-data.md`. **For Riot** lines are the design input.

## What was scored

All rankers rank the same test candidates (59,612 queries, 3,150,603
pairs). The model was not refit.

```
floor     global popularity among the candidates     (PRD floor stand-in)
v0_rule   opened-next count, then reverse count, views  (PRD baseline V0)
model     hgb_log1p, modeling/model.joblib            (V1)
hybrid    per-slice routing fixed on the train CV: model for long_tail
          and torso, V0 for new, dormant and head     (V1 as shipped)
```

Metrics use the **full truth**: every September next page from A, also
pages that no candidate rule found. So candidate misses count, unlike the
train CV (candidate-only ideal).

- Query side (the panel on A), per `q_slice`: nDCG@5 (primary, gain
  `log1p(r)`), recall@5, `recall_w@5` (click-weighted), hit@5.
- Item side (C as the true next page), per `item_slice`: recall@5 over
  the true next pages in that slice.
- "Weighted" = mean over query slices, weighted by the test population
  (long_tail 48.4%, torso 40.6%, head 10.2%, dormant 0.5%, new 0.3%).
- 95% CIs: paired bootstrap over queries, 1,000 draws.

## Results

### Query side: nDCG@5

Weighted, then new / dormant / long_tail / torso / head:

- floor: 0.0001; all slices 0.000-0.001.
- v0_rule: 0.8407; 0.222 / 0.130 / 0.733 / 0.945 / 0.990.
- model: 0.8443; 0.223 / 0.130 / 0.739 / 0.947 / 0.989.
- **hybrid: 0.8445; 0.222 / 0.130 / 0.739 / 0.947 / 0.990.**

Secondary (weighted): recall@5 V0 0.839, model 0.844, hybrid 0.843;
`recall_w@5` V0 0.739, model 0.742, hybrid 0.742; hit@5 V0 0.915, model
and hybrid 0.916. Coverage of the catalog: V0 4.7%, model 5.3%, hybrid
5.3%, floor under 0.01%.

### Lift over V0, nDCG@5, 95% CI

`hybrid` - `v0_rule`:

- weighted **+0.0037 [+0.0033, +0.0042]**;
- long_tail +0.0063 [+0.0055, +0.0071];
- torso +0.0017 [+0.0012, +0.0021];
- new, dormant, head: 0 (V0 ranks them).

`model` - `v0_rule` (no routing): weighted +0.0036 [+0.0032, +0.0040];
new +0.0006 [-0.0008, +0.0019] (inside the noise); head -0.0011
[-0.0016, -0.0005] (worse). The train CV result holds on test.

### Item side: recall@5 of true next pages, by the page's slice

- new (5,214 true pairs): V0 0.060, **model 0.046**, hybrid 0.057.
- dormant (3,358): 0.000 for every ranker.
- long_tail (65,182): V0 0.257, model 0.260, hybrid 0.260.
- torso (205,395): V0 0.289, model 0.292, hybrid 0.292.
- head (301,449): V0 0.234, model 0.234, hybrid 0.234.

Deltas, 95% CI:

- model - V0, new pages: **-0.014 [-0.018, -0.010]**: the model shows new
  pages less often than the rule does.
- hybrid - V0, new pages: -0.003 [-0.005, -0.001].
- long_tail: +0.003 for both [+0.002, +0.004]; torso +0.003.

### Candidate recall (the ceiling, from the build)

Query side: new 0.188, dormant 0.043, long_tail 0.734, torso 0.883, head
0.645. Item side: new 0.110, dormant 0.0003. No ranker can exceed these.

### Overfit

nDCG@5 weighted, same truth-based metric: model on train 0.8284, on test
0.8443. Test is higher than train, so there is no overfit gap. The
difference is the month: September's slice mix and traffic differ from
August's. V0 moves the same way (train 0.8247, test 0.8407), and the
model's lift over V0 is the same on both (+0.0037 train, +0.0036 test).

## Verdict

**Partial.** Against the V1 gate (`design/high-level.md`; the PRD has no
numeric bar, so the gate is the bar):

- Overall: passes. The hybrid beats V0 by +0.0037 nDCG@5, CI above 0.
- long_tail and torso: pass, CI above 0.
- head: routed to V0, so no loss.
- **new pages: not passed.** No gain on the query side (inside the
  noise), and the model alone shows new pages less often on the item side
  (-1.4 points). The candidate recall for new pages is 0.19, so most of
  the right pages never reach the ranker.
- The gain is real but small: about +0.4% nDCG@5. On the proxy, the model
  only re-weighs the click signals that V0 already uses.

## What it means

1. **The per-slice hybrid is the right way to ship V1.** It keeps the
   long_tail and torso gain and removes the head loss.
2. **A click-trained model is biased against new pages.** It learns that
   pages with traffic get clicked, so it pushes down pages with no
   history. This is the item-side cold-start problem in numbers.
3. **For Riot:**
   - Add item-side new-page recall@5 as a guardrail of the V1 gate: the
     model must not show new pages less often than V0.
   - The fixes are content and structure: candidate sources that find new
     pages, features that score them without clicks, and the V2
     exploration slot. See `research/page-content.md`, "Conclusions".
   - The proxy floor (global popularity) scores almost 0. Riot's floor is
     space-scoped popularity, which should do better; still, it confirms
     that "popular" is not "related".

## Notes

- The routing (which slices use the model) was fixed from the train CV in
  `03-train.md`, before the test was scored. It was not tuned on test.
- `test_scores.parquet` has every pair's score for the 4 rankers, so a
  metric change reruns only the metric code.
- Runs 7-9 in `modeling/experiments.json` (test_v0_rule, test_model,
  test_hybrid); `compare --ids 7 8 9` shows the hybrid best on nDCG@5 and
  `recall_w@5`, and V0 best on item-side new recall.

## Change log

- 2026-10-09: created.
