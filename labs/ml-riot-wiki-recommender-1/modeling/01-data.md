# 01 - Data

- Mode: Quick POC, 2026-10-08.
- Design docs: `spec/riot-wiki-article-recommender.md` was synthesized in
  this step (first `ml-modeling-*` run). The hashes match the current PRD and
  `design/high-level.md`.
- Code: `modeling/build_dataset.py` (build), `modeling/profile_data.py`
  (profile), `dashboard/eda.ipynb` (executed EDA).

## Proxy rule: Riot is the target, Wikipedia is evidence

No Riot wiki data exists in this sandbox. Every table below is built from
Wikipedia Clickstream. The proxy tests the method (candidates, label,
reranker, temporal eval). It does not set Riot's numbers.

- Each finding below has a **For Riot** line. That line is the design
  input. The proxy number is only the evidence for it.
- When the proxy and the Riot design differ, the Riot design wins. The
  proxy result is then a lower bound or a sanity check, and this file says
  which.

```
Riot design (target)            proxy in this step (evidence)
wiki.page_views, 14-day label   monthly click counts, 1-month label
distinct readers >= 3           clicks >= 10 (Wikimedia filter)
out-links, tree, entities, text none: only click edges
sessions, permissions, archive  none
~40k pages, a few thousand      3.8M pages, billions of clicks
  readers
```

## Dataset

The source is raw logs, so this step built the labeled table.

- **Unit.** One (source page `q`, candidate page `item`) pair.
- **Label.** `label = log1p(r)`. `r` is the label-month click count for the
  pair, and 0 when the pair is absent.
- **Candidates** (from the feature month only, union, deduplicated):
  - opened-next: the top 50 pages that readers of `q` opened next;
  - two-hop: the top 50 pages by sum over B of P(B|q) * P(C|B), each hop
    capped at 20;
  - reverse: the top 20 pages that send readers to `q`;
  - popular: the top 20 pages by in-clicks (backfill).
- **Truth tables** keep every label-month pair for the sampled queries, also
  pairs that no candidate source found. Recall metrics use them.

### Split: two cutoffs, one month apart

```
           2026-07           2026-08           2026-09
train   [ features ]      [  labels  ]
test                      [ features ]      [  labels  ]
        T_train = 2026-08-01            T_test = 2026-09-01
```

- Clickstream is monthly, so each window is one calendar month. This takes
  the place of the design's [T - 28 d, T) features and [T, T + 14 d) label.
- The train labels (August) end where the test labels start (September).
  No training label overlaps the test window.
- No seasonal event is named in the framing. Aug -> Sep includes the end of
  the northern-summer holidays, so the traffic mix shifts a little. That
  shift is part of what a temporal test must survive.
- Queries are sampled per split and stratified by bucket (seed 42). 2,111
  pages are in both query sets. This is allowed: production scores the same
  pages every night. No page id is a feature.
- **For Riot:** use the design windows (28-day features, 14-day labels),
  with the same two-cutoff rule: `T_train <= T_test - 14 days`.

### Size and sampling

- **Train: 100,000 query pages, 4.60% of the 2,173,164 source pages with
  August traffic.** 5,664,045 pairs.
- **Test: 50,202 query pages, 2.38% of the 2,112,678 source pages with
  September traffic.** 2,910,738 pairs.
- The candidate universe is not sampled: all 3,776,397 pages over the three
  months can be candidates.
- Small buckets get a minimum count (10,000 train, 5,000 test). Metrics are
  re-weighted to the population share of each bucket.

Buckets, by the query's out-clicks in the feature month:

- cold: 0. In train, 11,615 queries; 3,526 of them (30%) never appear in
  July at all. These are the closest match to a brand-new Riot page.
- tail (long-tail): 1-50. 30,072 queries.
- torso: 51-1000. 46,163 queries.
- head: more than 1000. 12,150 queries.

### Exclusions

- External sources (search, empty referrer, other sites) as source.
- `Main_Page` as source or candidate.
- Self pairs (q = item). Asserted 0.
- Pairs with fewer than 10 clicks a month (Wikimedia filter; the minimum n
  in all three files is 10).
- Bot traffic (Wikimedia filter on user agents).

Paths (git-ignored, under `<sandbox>/data/wikipedia-clickstream/modeling/`,
recorded in `01-data.json`):

- `pairs_{train,test}.parquet` - the labeled tables.
- `truth_{train,test}.parquet` - all label-month pairs per query.
- `queries_{train,test}.parquet` - queries, bucket, `seen_f`.
- `months/2026-0{7,8,9}.parquet`, `titles.parquet` - shared inputs for the
  features step.

The tables are parquet, not the CSV under `modeling/datasets/` that the
skill names. 8.6M rows as CSV is slow and large, and the project rule puts
generated data under `<sandbox>/data/`. Logged in `SKILL-IMPROVEMENTS.md`.

## Profile (train only)

- **Shape.** 5,664,045 rows, 9 columns, 157 MB in memory.
- **Nulls.** 0 in every column.
- **Label.**
  - Zero-inflated: 86.6% of pairs have label 0; 13.4% have label > 0.
  - Positive rate by bucket: head 32.7%, torso 10.2%, tail 4.1%,
    cold 1.4%.
  - When r > 0: median 30 clicks, p90 190, p99 1,493, max 140,110. Skew 56.5
    on r, 1.34 on `log1p(r)`. The log label removes almost all the skew.
- **Candidates per query.** 20 to 138, median 55.
- **Positives per query.** Median 3, mean 7.6, max 84.

### Candidate sources

Each source: its share of all candidate pairs, then the share of its pairs
with label > 0.

- **opened-next:** 14.5% of pairs; 85.4% positive.
- **reverse:** 11.0% of pairs; 44.5% positive.
- **two-hop:** 49.6% of pairs; 9.3% positive.
- **popular:** 35.3% of pairs; 0.02% positive.

### Candidate recall (the ceiling for any ranker)

The share of label-month next pages that the candidates contain. The
weighted value counts clicks.

- **cold:** train 0.183 (weighted 0.062); test 0.171 (weighted 0.047).
- **tail:** train 0.760 (0.798); test 0.782 (0.790).
- **torso:** train 0.851 (0.933); test 0.873 (0.939).
- **head:** train 0.671 (0.919); test 0.681 (0.926).

## Findings and what they mean for Riot

1. **Cold pages are much harder on a real time split.**
   - Proxy: cold candidate recall is 0.17-0.18, against 0.298 in the
     monkey-mode thinning run. 71.9% of cold train queries have no positive
     candidate at all, so every model scores 0 on them.
   - Cause: a cold proxy page has only reverse edges and global
     popularity. The proxy has no out-links, tree, entities or text.
   - **For Riot:** a click- and link-only V1 can't serve new pages. The
     structure sources in `research/cold-start.md` (the page's own
     out-links, page tree, shared entities, topic similarity with
     duplicates removed) are a requirement for V1, not an extra. Riot has
     these signals on the day a page is created. The proxy's cold score is
     a lower bound for Riot, not an estimate.
2. **Global popularity is a poor candidate source.**
   - Proxy: 35% of all candidate pairs, 0.02% positive.
   - **For Riot:** keep it only as the final fallback. Use "most-read pages
     in the same space" (the PRD floor) instead, because a space is a
     topic. Don't give global popularity a place in the 100 candidates.
3. **Two-hop is large and weak; reverse is small and strong.**
   - Proxy: two-hop is half the pairs at 9% positive. Reverse is 11% of
     pairs at 45% positive.
   - **For Riot:** keep both. Two-hop gives reach for long-tail pages; the
     reranker must learn to discount it. Back-links are a day-one signal
     in Riot (from `wiki.links`), not only a click signal.
4. **The label is sparse and heavy-tailed.**
   - Proxy: 86.6% zeros, and r spans 10 to 140k.
   - **For Riot:** counts are far smaller (about 40k pages, a few thousand
     readers). With 14 days and a 3-reader minimum, most pairs will be 0,
     and many pages will have no positive pair. Check the Riot positive
     rate per bucket first. If it is too low, use a 28-day label window
     before you lower the 3-reader rule. This is a design question for
     `design/high-level.md`; flagged, not changed.
5. **Head pages hit the candidate cap.**
   - Proxy: head recall is 0.67 by page but 0.92 by clicks. The cap of 50
     opened-next pages drops many rare targets of very busy pages.
   - **For Riot:** few wiki pages have more than 50 distinct next pages
     with 3 or more readers. The 100-candidate cap is enough. No change.

## Quality flags and cleaning

Impossible values: none found. No duplicate pairs, no self pairs, no nulls,
no negative counts. Nothing was cleaned.

Unusual values, left as they are and documented:

- Very large r (up to 140,110). Real traffic. The log label handles it.
- Zero-inflated label. Real. The features and train steps must handle it
  (the label sweep in `design/high-level.md` covers it).

Proxy gaps, documented as risks (they can't be fixed in the proxy):

- Click counts, not distinct readers. One reader's repeat clicks count more
  than once.
- Label 0 means r < 10, not r = 0.
- No session ids, page text, permissions or archive status.
- Monthly windows, not 28 and 14 days.

## Dashboard

- `dashboard/eda.ipynb`: executed, 0 error cells.
- `dashboard/app.py`: copied from the skill template, running at
  http://localhost:8502 (`dashboard/.port`, `dashboard/.pid`).
