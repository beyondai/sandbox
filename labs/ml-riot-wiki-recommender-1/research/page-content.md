# Page content for the proxy: feasibility and work

Written 2026-10-09. Status: **deferred** (user decision, 2026-10-09). The
design still assumes these features (see "Design assumption").

Purpose: get Wikipedia page text (and the link and category structure) so
the POC can test the Riot text, embedding and structure features on the
proxy (`modeling/02-features.md`, "Text and embedding features").

## Conclusions: how much does page content matter for new pages?

Short answer. It is safe to say that page content and structure are
**necessary** for new pages: they are the only signals a new page has,
and the click signals measurably fail. It is **not yet safe** to say how
large the gain is, or which content signal matters most. The proxy has no
text, links or tree, so that part is unmeasured.

```
                       new pages               long-tail pages (contrast)
candidate recall       0.19  (query side)      0.73
nDCG@5 (full truth)    0.22  V0 = model        0.73 -> 0.74 with the model
item-side recall@5     0.060 V0, 0.046 model   0.257 -> 0.260
                               ^ model is worse
```

Evidence (test split, `modeling/04-evaluate.md`; build,
`modeling/01-data.md`):

1. **Clicks can't find the right page for a new page.** Query-side
   candidate recall is 0.19 for new pages and 0.04 for dormant pages,
   against 0.73 for long-tail pages. For 55% of new pages (train), no candidate
   is a true next page. A ranker can't fix a page that isn't in the list.
2. **More ML on clicks doesn't help, and can hurt.** The GBDT gains
   nothing on new pages on the query side (+0.0006, inside the noise). On
   the item side it shows new pages **less often** than the V0 rule
   (recall@5 0.046 vs 0.060, CI [-0.018, -0.010]): a click-trained model
   learns "pages with traffic get clicked" and pushes down pages with no
   history.
3. **At creation, content and structure are all a page has.** A new Riot
   page has its text, its own links, its place in the page tree, its
   author, owner team, labels and template, and the entities it names. It
   has no clicks. So any gain on new pages must come from these signals.
   This follows from the setup; it does not need a measurement.

What is not shown yet:

4. **The size of the gain.** The upper bound is the long-tail level:
   about nDCG@5 0.73 and item-side recall@5 0.26, against 0.22 and 0.06
   for new pages today. The real gain is somewhere below that. The
   deferred proxy experiment (below) measures it.
5. **Which content signal matters most.** For Riot, structure (own
   out-links, page tree, shared entities) is expected to beat plain text
   similarity: structure encodes logical connection, while text
   similarity also promotes near-duplicates (PRD, scope). Text is still
   needed: for the embedding candidate source (with near-duplicate
   collapse), for borrowed clicks, and as a feature.
6. **The overall metric barely moves.** New pages are about 0.3% of
   source pages in the proxy, and about 100 of 40k pages a week in Riot.
   A large new-page gain is a small change in weighted nDCG@5. So the
   value must be judged on the new-page slice, the item-side new-page
   recall, and the online "days to first useful click", not on the
   overall number.

Suggested wording for the design and for stakeholders:

- "Page content and structure are required for new pages. Click-based
  methods find the right page for only 19% of new pages, and a
  click-trained model shows new pages less often than a simple rule."
- "The expected gain is up to the long-tail level for new pages; the
  exact size will be measured on Riot data (or on the proxy with the link
  and text dumps)."
- Do not say "text embeddings will give a large gain" until it is
  measured.

What this changes in the design (`design/high-level.md`):

- V1 keeps the content and structure candidate sources and features
  (already assumed).
- The V1 gate gets an item-side guardrail: the shipped ranker must not
  show new pages less often than V0.
- The V2 exploration slot stays: it is the item-side fix that does not
  depend on the ranker learning to trust new pages.

## Scope

- Pages that matter: every page that is a query, a candidate or a true
  next page in either split: **1,777,602 pages, 47% of the 3,776,397-page
  catalog**.
- Text needed per page: title, headings and the lead section (first
  about 300 words). Not the full body.
- Time: text as of each cutoff. Train T = 2026-08-01, test T =
  2026-09-01. Text from after T is a mild leak: a page can gain text and
  links because it got traffic.
- Disk: about 64 GB free.

## Options for page text

### A. XML dumps per cutoff (recommended)

- Files: `enwiki-20260801-pages-articles-multistream.xml.bz2` (train)
  and `enwiki-20260901-...` (test). About 27 GB each. Both runs are
  still on dumps.wikimedia.org (runs 20260601 to 20261001 are listed).
- Work:
  1. Download one dump, stream-decompress it, and keep only the
     1.78M pages in scope. Never write the uncompressed XML.
  2. Parse wikitext to plain text (`mwparserfromhell`, a new package via
     `uv add` at the sandbox root). Keep title, headings, lead.
  3. Write `data/wikipedia-clickstream/text/text_<YYYYMMDD>.parquet`
     (about 1 GB). Delete the 27 GB dump, then do the second one.
- Time: download about 1-3 hours per dump (mirror speed); parse about 1-2
  hours per dump with all CPU cores. Unattended.
- Pros: text as of each cutoff (no leak). Includes every page created up
  to the dump date, so the new pages are covered.
- Cons: 54 GB of downloads; the dump for a date is written over several
  days after that date, so "as of T" is approximate (a few days late).

### B. One current dump (faster, small leak)

- `enwiki-20261001-pages-articles-multistream.xml.bz2`, 26.9 GB. We
  already have its index.
- Same work as A, done once. Half the time and download.
- Con: text is 1-2 months after the cutoffs. Acceptable for a first test
  of "does text help new pages"; not for final numbers.

### C. Hugging Face `wikimedia/wikipedia` (20231101.en)

- 11.6 GB of clean text, no parsing.
- **Not usable for our main question:** the snapshot is from November
  2023, so it has none of the new pages of July to September 2026.

### D. MediaWiki API (TextExtracts, 20 pages per call)

- Clean lead text, no parsing. The API rate-limits us (HTTP 429 seen
  during the page-age calibration); about 1 call per second is safe.
- 1.78M pages: about 89k calls, about 25 hours. Too slow for all pages.
- Good for a subset: the about 15k new pages take about 15 minutes.
- Text is current, not as of T (same leak as B).

### E. Wikimedia Enterprise snapshots

- Clean HTML and structured content. Needs an account; free-tier limits.
  Not worth it for a POC.

## Structure dumps: the other Riot day-one signals

The proxy has only click edges. Riot has links, page tree and labels from
the day a page is created. These dumps are the closest proxy, and they
address the low candidate recall for new pages (0.19) more directly than
text:

- `pagelinks.sql.gz` (7.2 GB) + `linktarget.sql.gz` (1.4 GB): every
  wikilink, clicked or not. Proxy for Riot `wiki.links`: a new page's own
  out-links and its back-links.
- `categorylinks.sql.gz` (2.5 GB): categories. Proxy for Riot spaces,
  labels and page-tree siblings (pages in the same small category).
- Work: stream-parse the SQL inserts and keep rows that touch in-scope
  pages. pagelinks has over 1 billion rows; filtering on the fly keeps
  the output small. About 1-2 hours, unattended. Same leak note: use the
  dump nearest each cutoff.

## Features and checks this enables

```
text dump    -> lead text -> TF-IDF, embeddings -> cos_tfidf, cos_emb,
                                                   borrowed_clicks,
                                                   near-duplicate groups,
                                                   embedding candidate source
pagelinks    -> link graph -> own out-links, back-links (candidate source)
categories   -> groups     -> same-category siblings (candidate source)
                         |
                         v
         candidate recall for new and dormant pages, query and item side
         (the number to move: 0.19 and 0.04 today)
```

- Embeddings: a small sentence-embedding model (about 30M parameters) on
  1.78M leads is about 1-2 hours on the laptop CPU, faster on the Apple
  GPU (MPS). Needs `uv add sentence-transformers` (pulls torch, about
  1-2 GB). The features skill excludes embeddings from a POC for laptop
  resources; this is a user-approved exception if we go ahead.
- TF-IDF: scikit-learn, minutes, no new package.
- Nearest-neighbour search over 1.78M vectors: `hnswlib` or `faiss-cpu`
  (new package), minutes.

## Recommended plan

1. Structure first: pagelinks + linktarget + categorylinks from the dump
   nearest each cutoff. Cheapest test of the Riot day-one sources.
2. Text second: option B (one current dump) for a first answer; option A
   if the result is worth reporting.
3. Re-run candidate recall per slice and side; then re-run the feature
   importance with the new features.

Total: about one working day, mostly unattended download and parse time.

## For Riot

- Much easier than the proxy. About 40k pages from the wiki REST export,
  with text, links, tree and labels in one place. Full text and embedding
  backfill: minutes. Nightly update: about 100 new and 1k edited pages a
  week.
- No time-travel problem: the nightly batch reads the current page.
- Training data still needs text as of each cutoff. Keep the page
  version history (the wiki keeps it) or snapshot the export each night.

## Design assumption

- The Riot design (V1 in `design/high-level.md`) includes the text,
  embedding and structure features and candidate sources, whether or not
  the proxy is ever extended.
- Until this plan runs, every proxy result for new and dormant pages is a
  lower bound, and every modeling doc says so.
- The train step should keep the model and feature code ready for these
  columns: missing-value safe (GBDT handles nulls), with one flag per
  candidate source.

## Change log

- 2026-10-09: created; deferred by the user. The design assumes the
  features anyway.
- 2026-10-09: added "Conclusions" from the test evaluation: content and
  structure are necessary for new pages; the size of the gain is not
  measured yet.
