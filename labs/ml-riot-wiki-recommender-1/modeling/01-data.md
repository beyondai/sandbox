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
- **Negatives.** The label is graded, so a negative is a candidate pair
  with label 0. All negatives are hard negatives: pages that a candidate
  rule chose for the query, but that readers didn't open next (r < 10).
  - No random negatives and no down-sampling, so no correction is needed.
    About 6.7 label-0 pairs per positive pair (train).
  - Train and test use the same candidate rules, so test negatives follow
    the production distribution: what the ranker will really see.
  - **For Riot:** use the same rule. After launch, add impressed but not
    clicked panel pages as a second hard-negative type, with slot position
    as a feature (high-level, Feedback loop). Random negatives add little,
    because the ranker never sees random pages.

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
- Queries are sampled per split and stratified by query slice (seed 42).
  3,718 pages are in both query sets. This is allowed: production scores
  the same pages every night. No page id is a feature.
- **For Riot:** use the design windows (28-day features, 14-day labels),
  with the same two-cutoff rule: `T_train <= T_test - 14 days`.

### Size and sampling

- **Train: 117,591 query pages, 5.41% of the 2,173,164 source pages with
  August traffic.** 6,185,251 pairs.
- **Test: 59,612 query pages, 2.82% of the 2,112,678 source pages with
  September traffic.** 3,150,603 pairs.
- The candidate universe is not sampled: all 3,776,397 pages over the three
  months can be candidates.
- Queries are stratified by query-side slice. Small slices get a minimum
  count (10,000 train, 5,000 test), or all pages when fewer exist. Metrics
  are re-weighted to the population share of each slice.

### Slices: age axis and traffic axis, on both sides

Cold-start (new) and long-tail (rarely used) are different problems, so
they are separate slices (PRD, Metrics - offline, Slices). Every page gets
two slices at each cutoff T: `q_slice` for the panel on it (query side) and
`item_slice` for it as a recommendation (item side).

```
                 age (page id)        traffic (feature month)
new          created < 14 d before T
             or after T
dormant      established              0 recorded views
long_tail    established              activity <= p50 of pages with activity
torso        established              p50 < activity <= p90
head         established              activity > p90

activity:  query side = out-clicks to wiki pages; item side = in-clicks
           from wiki pages. Pages with views but 0 activity are long_tail.
```

- **Age on the proxy.** Clickstream has no creation date. Page ids are
  given out in creation order, so `modeling/calibrate_page_age.py` maps
  dates to page ids with the Wikipedia API (`modeling/page_id_dates.json`,
  about 270k ids a month), and the 2026-10-01 dump index maps titles to
  page ids. 19,860 catalog pages (0.5%) have no page id (renamed or
  deleted); they count as established.
- **Thresholds** (train; test is within 3%):
  - query side: p50 = 82 out-clicks, p90 = 1,344;
  - item side: p50 = 79 in-clicks, p90 = 1,101.
- **Query counts.**
  - Train: new 8,252 (all: 6,219 created after T, 2,033 created less than
    14 days before T), dormant 10,000 of 11,438, long_tail 50,690, torso
    38,649, head 10,000.
  - Test: new 5,000 of 5,581, dormant 5,000 of 10,838, long_tail 24,202,
    torso 20,291, head 5,119.
- **For Riot:** the same definitions, with `wiki.pages.created` for age,
  `wiki.page_views` for dormant, and distinct readers (not clicks) for
  activity. Riot's tiers will be far smaller numbers; percentiles keep the
  definitions valid at any scale.

### Exclusions

- External sources (search, empty referrer, other sites) as source. They
  still count toward a page's views.
- `Main_Page` as source or candidate.
- Self pairs (q = item). Asserted 0.
- Pairs with fewer than 10 clicks a month (Wikimedia filter; the minimum n
  in all three files is 10).
- Bot traffic (Wikimedia filter on user agents).

Paths (git-ignored, under `<sandbox>/data/wikipedia-clickstream/modeling/`,
recorded in `01-data.json`):

- `pairs_{train,test}.parquet` - the labeled tables, with `q_slice` and
  `item_slice`.
- `truth_{train,test}.parquet` - all label-month pairs per query, with both
  slices.
- `queries_{train,test}.parquet` - queries, `q_slice`, age, views.
- `pages_{train,test}.parquet` - every catalog page: age, views, activity,
  both slices.
- `months/2026-0{7,8,9}.parquet`, `months/views_2026-0{7,8,9}.parquet`,
  `titles.parquet` - shared inputs for the features step.

The tables are parquet, not the CSV under `modeling/datasets/` that the
skill names. 9.3M rows as CSV is slow and large, and the project rule puts
generated data under `<sandbox>/data/`. Logged in `SKILL-IMPROVEMENTS.md`.

## Profile (train only)

- **Shape.** 6,185,251 rows, 10 columns, 206 MB in memory.
- **Nulls.** 0 in every column.
- **Label.**
  - Zero-inflated: 87.1% of pairs have label 0; 12.9% have label > 0.
  - Positive rate by query slice: head 35.0%, torso 12.0%, new 9.2%,
    long_tail 4.1%, dormant 0.65%.
  - Positive rate by item slice: long_tail 23.0%, torso 21.1%, new 17.5%,
    head 9.6%, dormant 7.7%. (Head items are often popularity backfill,
    which is rarely right.)
  - When r > 0: median 30 clicks, p90 190, p99 1,483, max 370,264. Skew
    180 on r, 1.34 on `log1p(r)`. The log label removes almost all the
    skew.
- **Candidates per query.** 20 to 137, median 46.
- **Positives per query.** Median 2, mean 6.8, max 85.

### Candidate sources

Each source: its share of all candidate pairs, then the share of its pairs
with label > 0.

- **opened-next:** 14.0% of pairs; 85.5% positive.
- **reverse:** 10.5% of pairs; 44.8% positive.
- **two-hop:** 47.5% of pairs; 9.4% positive.
- **popular:** 38.0% of pairs; 0.02% positive.

### Candidate recall (the ceiling for any ranker)

The share of label-month next pages that the candidates contain. The
weighted value counts clicks. Test split (train is similar, except where
noted).

Query side (the panel on page A):

- **new:** 0.188 (weighted 0.252). Train: 0.348.
- **dormant:** 0.043 (0.010).
- **long_tail:** 0.734 (0.783).
- **torso:** 0.883 (0.950).
- **head:** 0.645 (0.916).

Item side (page C as the true next page):

- **new:** 0.110 (0.144). Train: 0.243.
- **dormant:** 0.0003 (0.000).
- **long_tail:** 0.569 (0.530).
- **torso:** 0.702 (0.753).
- **head:** 0.695 (0.819).

Queries with no positive candidate (train): dormant 86.7%, new 55.3%,
long_tail 17.4%, torso and head 0%. Every model scores 0 on these.

## Findings and what they mean for Riot

1. **New and dormant pages are separate problems, and the data shows it.**
   - Proxy: on the query side, candidate recall is 0.19 for new pages and
     0.04 for dormant pages. Long-tail pages are at 0.73, close to torso.
   - Long-tail is mostly a ranking problem: the right page is usually in
     the candidates. New and dormant pages are a candidate problem: the
     right page is usually missing.
   - **For Riot:** V1 needs the structure candidate sources from
     `research/cold-start.md` (own out-links, page tree, shared entities,
     topic similarity with duplicates removed). Riot has them on the day a
     page is created; the proxy has none. The proxy numbers for new and
     dormant pages are lower bounds for Riot, not estimates.
2. **On the item side, click-based candidates almost never surface new or
   dormant pages.**
   - Proxy: a true next page that is new is found 11% of the time; a
     dormant one almost never (0.03%).
   - **For Riot:** this is the case for the exploration slot for new pages
     (V2) and for structure sources that can point to a page with no
     clicks. Without them, a new runbook is never recommended, however
     relevant.
3. **Dormant query pages on Wikipedia are mostly sudden spikes.**
   - Proxy: a dormant page that has next-page traffic in the label month
     usually became news. Its readers go to pages that last month's clicks
     can't predict.
   - **For Riot:** the same pattern is an old service page that matters
     again during an incident. Structure and entity links (service ->
     runbook -> post-mortem) are the only signal that works there.
4. **Global popularity is a poor candidate source.**
   - Proxy: 38% of all candidate pairs, 0.02% positive.
   - **For Riot:** keep it only as the final fallback. Use "most-read pages
     in the same space" (the PRD floor) instead. Don't give global
     popularity a place in the 100 candidates.
5. **Two-hop is large and weak; reverse is small and strong.**
   - Proxy: two-hop is about half the pairs at 9% positive. Reverse is 11%
     of pairs at 45% positive.
   - **For Riot:** keep both. Back-links are a day-one signal in Riot (from
     `wiki.links`), not only a click signal.
6. **The label is sparse and heavy-tailed.**
   - Proxy: 87% zeros, and r spans 10 to 370k.
   - **For Riot:** counts are far smaller (about 40k pages, a few thousand
     readers). With 14 days and a 3-reader minimum, most pairs will be 0.
     Check the Riot positive rate per slice first. If it is too low, use a
     28-day label window before you lower the 3-reader rule. This is a
     design question for `design/high-level.md`; flagged, not changed.
7. **Head pages hit the candidate cap.**
   - Proxy: head recall is 0.65 by page but 0.92 by clicks. The cap of 50
     opened-next pages drops many rare targets of very busy pages.
   - **For Riot:** few wiki pages have more than 50 distinct next pages
     with 3 or more readers. The 100-candidate cap is enough. No change.

## Quality flags and cleaning

Impossible values: none found. No duplicate pairs, no self pairs, no nulls,
no negative counts. Nothing was cleaned.

Unusual values, left as they are and documented:

- Very large r (up to 370,264). Real traffic. The log label handles it.
- Zero-inflated label. Real. The features and train steps must handle it
  (the label sweep in `design/high-level.md` covers it).

Proxy gaps, documented as risks (they can't be fixed in the proxy):

- Click counts, not distinct readers. One reader's repeat clicks count more
  than once.
- Label 0 means r < 10, not r = 0.
- No session ids, page text, permissions or archive status.
- Monthly windows, not 28 and 14 days.
- Page age is approximate: page ids calibrated to dates, not creation
  times. 0.5% of pages have no page id and count as established.
- Dormant means 0 recorded views, and views under 10 per referrer are not
  recorded. Some "dormant" pages had a few views.

## Dashboard

- `dashboard/eda.ipynb`: executed, 0 error cells.
- `dashboard/app.py`: copied from the skill template, running at
  http://localhost:8502 (`dashboard/.port`, `dashboard/.pid`).

## Change log

- 2026-10-08: created.
- 2026-10-08: replaced the single out-click bucket (cold, tail, torso,
  head) with the PRD slices: age (new, from calibrated page ids) and
  traffic (dormant, long_tail, torso, head), on the query and item sides.
  Rebuilt both splits. Cold-start and long-tail now show different
  failure modes (candidate recall 0.19 new, 0.04 dormant, 0.73 long_tail).
