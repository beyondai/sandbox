# 02 - Features

- Mode: Quick POC, 2026-10-09.
- Design docs: the spec hashes match the current PRD and
  `design/high-level.md`. No change since the data step.
- Code: `modeling/features.py` (`transform(pairs, split)`),
  `modeling/feature_importance.py` (selection check).
- Proxy rule: as in `01-data.md`. Each group has a **For Riot** line, which
  is the design input.

## How the features are built

- **Unit.** One (source page `q`, candidate page `item`) pair, as in
  `01-data.md`.
- **History only.** Every feature comes from the split's feature month:
  July for train, August for test. The label month is never read.
- **Nothing is fit.** No feature uses the label (no target encoding, no
  aggregates of r), so leave-one-out is not needed. `transform` is the same
  function for train and test, and test uses its own (later) history, as
  production would.
- **Prediction time.** Each feature is known at the nightly batch: counts
  up to T, page age at T, and which rules proposed the candidate.

```
feature month (history before T)            pair (A, C)
  A -> C clicks  ---------------------->  opened-next group
  C -> A clicks  ---------------------->  reverse group
  A -> B -> C    ---------------------->  two-hop group
  C's in/out/views/age ---------------->  item group
  A's out/views/age  ------------------>  query group
  candidate rules    ------------------>  cand_flags group
```

## Feature list (23)

### Opened-next: A -> C (the V0 baseline signal)

- `log_n_ac`: log1p of clicks A -> C. 0 when there is no edge.
- `p_c_given_a`: share of A's out-clicks that went to C.
- `rank_ac`: rank of C among A's out-edges. Null when there is no edge.
- `is_link_ac`: 1 when the A -> C clicks came from a link in A, 0 for
  other. Null when there is no edge.
- Reason: the framing ranks by future opened-next readers. Past
  opened-next is the strongest known predictor (monkey mode; correlation
  with the label 0.93 here).
- **For Riot:** distinct readers who opened C right after A in 28 days,
  with the 3-reader rule. `is_link_ac` becomes "C is linked in A's body",
  from `wiki.links`, known even with no clicks.

### Reverse: C -> A

- `log_n_ca`: log1p of clicks C -> A.
- `p_a_given_c`: share of C's out-clicks that went to A.
- Reason: reverse edges gave almost all the cold-page lift in monkey mode,
  and reverse candidates are 45% positive (`01-data.md`).
- **For Riot:** back-links from `wiki.links` (day one), plus reverse
  opened-next readers.

### Two-hop: A -> B -> C

- `twohop`: sum over B of P(B|A) * P(C|B), each hop capped at 20.
- `twohop_paths`: the number of such B pages.
- Reason: two-hop is half the candidates at 9% positive. The ranker needs
  a score to tell good two-hop pages from weak ones.
- **For Riot:** the same, over opened-next and link edges. Page-tree
  siblings are a special two-hop path (A -> parent -> C).

### Candidate page C

- `log_in_c`, `log_out_c`, `log_views_c`: log1p of in-clicks, out-clicks
  and views of C.
- `log_in_c_per_day`: in-clicks per day that C existed in the window
  (age clipped to 1-31 days).
- `item_age_days`: age of C at T, from calibrated page ids. Pages older
  than the first calibration point get 365. Null for 0.3% (no page id).
- `item_is_new`: C was created less than 14 days before T, or after T.
- Reason: the item-side slices (`01-data.md`); per-day counts so that a
  new page with few days of traffic is not ranked as long-tail
  (`design/high-level.md`, Slices).
- **For Riot:** `wiki.page_views`, `wiki.pages.created`. Add last-edit age
  and status (archived pages are filtered, not scored).

### Source page A

- `log_out_a`, `log_views_a`: log1p of A's out-clicks and views.
- `q_age_days`, `q_is_new`: as for C.
- Reason: the query-side slices. A page with little history should lean
  on reverse and two-hop signals; these features let the model learn
  that switch.
- **For Riot:** the same sources.

### Candidate rules

- `cand_opened_next`, `cand_twohop`, `cand_reverse`, `cand_popular`: 1
  when that rule proposed C.
- `n_sources`: how many rules proposed C.
- Reason: agreement between rules is cheap evidence.
- **For Riot:** one flag per Riot candidate source (links, page tree,
  entities, topic, borrowed clicks, opened-next, space-popular).

## Text and embedding features (Riot design, not built in the POC)

These features are part of the Riot design. The POC has no page text, so
they are not built or measured yet. They target exactly the slices where
the click features fail: new and dormant pages (candidate recall 0.19 and
0.04, `01-data.md`). Feasibility of getting proxy text:
`research/page-content.md`.

```
page text (title, headings, lead)
   |-- TF-IDF vector -----------> cos_tfidf(A, C)
   |-- sentence embedding ------> cos_emb(A, C), nearest-page candidates,
   |                              near-duplicate groups (cos > 0.9)
   |-- entity extraction -------> shared_entities(A, C)
   '-- nearest warm pages ------> borrowed_clicks(A, C)
```

### Features

- `cos_tfidf`: cosine of TF-IDF vectors (title + headings + lead).
  Reason: cheap, explainable topic match; catches exact service and
  system names that a generic embedding can blur.
- `cos_emb`: cosine of sentence embeddings of the same text. Reason:
  topic match across different wording ("rollback" vs "revert a
  deploy").
- `title_overlap`: shared title tokens, without stop words. Reason: wiki
  titles name the system ("Valorant Deploy Runbook").
- `shared_entities`, `entity_jaccard`: count and Jaccard of shared
  services, repos, Jira keys, Slack channels. Reason: the strongest
  logical-connection signal for internal docs (`research/cold-start.md`).
- `borrowed_clicks`: for the 10 warm pages nearest to A by embedding, the
  sum of their opened-next share to C. Reason: content-to-behavior
  transfer; a new page inherits the click pattern of similar old pages.
- `same_template`, `template_pair`: the page types of A and C (post-mortem,
  runbook, design spec). Reason: some type pairs are strong (post-mortem
  -> runbook of the same service).
- Cheap text signals for C: length, heading count, code-block count,
  days since last edit. Reason: stubs and stale pages are rarely useful.

### Uses besides features

- **Candidate source.** The top 50 pages by `cos_emb`, after near-duplicate
  collapse. This is the change that can raise candidate recall for new
  and dormant pages. A feature can only rank what a candidate rule found.
- **Near-duplicate collapse.** Groups with cosine over about 0.9 show one
  page (PRD, scope). Duplicates are a filter, not a positive signal.

### Riot cost and model choice

- About 40k pages, about 100 new and 1k edited pages a week. A full
  embedding backfill is minutes on CPU; the weekly update is seconds.
- Model: the internal embedding service if one exists (PRD, Team - reuse).
  Otherwise a small open sentence-embedding model (about 30M parameters,
  384 dimensions) run in the nightly batch. Fine-tuning on opened-next
  pairs is a V2+ option, only if it passes the complexity gate.
- Long pages: embed title + headings + lead (first about 300 words), not
  the full body. Runbooks and specs are long; the lead says what the page
  is about.
- Permissions: embeddings of restricted pages are computed like any
  other. The serve-time permission filter removes them from the panel.

### POC status

- Not built: no page text in the proxy. The features skill also excludes
  embeddings from a POC (laptop resources). The user asked to keep them in
  the design discussion (2026-10-09).
- To test them on the proxy, first get page text (see
  `research/page-content.md`), then re-run candidate recall for the new
  and dormant slices with an embedding candidate source.
- Getting the proxy data is deferred (user, 2026-10-09). The design
  assumes these features: they are in the V1 feature list in
  `design/high-level.md`, and the train step must accept them as extra,
  possibly null, columns.

## Selection

### Screen (`feature_selector.py`, 200k-row train sample)

Top 5: `log_n_ac` 0.875, `cand_opened_next` 0.800, `log_n_ca` 0.554,
`p_c_given_a` 0.526, `cand_reverse` 0.495. Bottom 3: `is_link_ac` 0.242,
`q_age_days` 0.204, `item_age_days` 0.164. A rough screen only; no
feature is dropped on it.

### Importance on held-out train queries (`feature_importance.py`)

- Setup: 10% of train queries held out (11,625 queries, 612k pairs). A
  small HistGradientBoosting regressor on `log1p(r)` (200 trees, 31
  leaves, learning rate 0.1), fit on half of the other rows (2.79M). Score:
  nDCG@5 over the candidates. The test split is not used.
- Base nDCG@5: all 0.772, new 0.416, long_tail 0.776.

Permutation drop in nDCG@5 (all / new / long_tail), largest first:

- `log_n_ac`: 0.536 / 0.281 / 0.454.
- `is_link_ac`: 0.016 / 0.011 / 0.031.
- `p_a_given_c`: 0.014 / 0.011 / 0.031.
- `rank_ac`: 0.013 / 0.008 / 0.027.
- `log_n_ca`: 0.011 / 0.011 / 0.021.
- Every other feature: below 0.005.

Drop a whole group and refit (all / new / long_tail):

- opened-next: 0.047 / 0.031 / 0.016.
- reverse: 0.001 / 0.001 / 0.002.
- two-hop: 0.001 / -0.001 / 0.001.
- item, query, candidate flags: 0.000 or less.

Reading:

- The opened-next count carries almost all the signal on the proxy. When
  the group is removed, the reverse and flag features recover most of it
  (0.536 permutation drop, but only 0.047 group drop).
- The reverse and two-hop groups add about 0.001-0.002. The item, query,
  age and flag groups add nothing measurable. No CI was computed, so
  values under about 0.002 are treated as noise.

### Decision: keep all 23

- Cost: every feature is one join on tables we already build. No new
  pipeline, no new data source.
- The groups that add nothing on the proxy target the cases the proxy
  can't create. New and dormant pages almost never reach the candidates
  here (candidate recall 0.19 and 0.04, `01-data.md`), so age and
  per-day features have nothing to act on. In Riot, the structure
  candidate sources bring new pages into the candidates, and then age and
  per-day counts decide how much to trust their few clicks.
- **For Riot:** re-run this importance check on Riot data with the
  structure sources. Drop a group only if its drop is still inside the
  noise there.

## Tried and dropped

- **Co-citation** (pages X that link to both A and C): the closest proxy
  for page-tree siblings. Dropped for the POC: hub pages make the join
  explode (millions of X -> C rows). **For Riot:** the page tree gives
  siblings directly, so this is not needed.
- **Target encoding of page ids:** dropped. It would memorize pages, and
  new pages have no id history. The framing ranks pairs, not ids.
- **Cyclical time features:** no row timestamps in monthly counts. **For
  Riot:** possible later (weekday vs weekend reading), not in V1.
- Text and embedding features are not dropped. They are Riot design
  features with no proxy data yet. See "Text and embedding features".

## Output table

- Train: `<sandbox>/data/wikipedia-clickstream/modeling/features_train.parquet`
  (6,185,251 rows: `q`, `item`, `q_slice`, `item_slice`, `r`, `label`
  and the 23 features). Git-ignored.
- Test: not written here. `ml-modeling-evaluate` calls
  `transform(pairs_test, "test")`, which uses August history only.
- Missing values: `rank_ac` and `is_link_ac` are null for 85.8% of pairs
  (no A -> C edge); the age features are null for under 0.6%. The tree
  model handles nulls natively; a linear model needs a missing flag.

## Change log

- 2026-10-09: created.
- 2026-10-09: text and embedding features moved from "dropped" to a
  Riot design section (user request); not built in the POC.
