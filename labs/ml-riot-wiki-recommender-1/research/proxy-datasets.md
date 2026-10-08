# Proxy datasets for a "related article" wiki recommender

Researched 2026-10-08. Goal: public text plus real behavior/relevance labels
that stand in for an internal wiki, so we can run a laptop-scale content
baseline (TF-IDF / sentence-embedding kNN) scored by recall@10 and nDCG@10 on
held-out (source -> next article) pairs.

Number labels used below:

- **published**: read directly from a listing page, HTTP `Content-Length`,
  archive metadata, an archive header, or an official API.
- **measured**: counted by me from a small slice (a few MB) of the real file.
- **derived**: my arithmetic on published/measured numbers. Treat as +/- 30%
  unless stated.

## TL;DR

| | Wikipedia Clickstream (enwiki) | Stack Exchange dump (unix / serverfault) |
|---|---|---|
| Labels | (prev, curr, type, n) click counts | PostLinks: "linked" and "duplicate" |
| Granularity | monthly only, since 2017-11 | quarterly full snapshots |
| Latest | 2026-09 (posted 2026-10-03) | 2026-06-30 (posted 2026-08-17) |
| One release | 479 MB gz, ~1.6 GB tsv, ~35M rows | unix 759 MB 7z; serverfault 908 MB 7z |
| Label count | millions of article pairs | unix 68,607; serverfault 35,562 links |
| Text | separate (API, dump, or HF) | in the same archive (Posts.xml) |
| License | CC0 (clicks); CC BY-SA (text) | CC BY-SA 2.5/3.0/4.0 |
| Slice cost | ~0.6-1 GB, ~15-25 min | ~240-300 MB download, ~15 min |

Recommendation: **start with Wikipedia Clickstream** on a ~10k-article
technical cluster. It is the only one of the two with real navigation
behavior ("read A, then went to B"), which is exactly the internal-wiki task,
and the labels are dense and graded. Use Stack Exchange unix PostLinks second,
as a sparse, editor-curated "related content" check that is less dominated by
existing hyperlinks.

## 1. Wikipedia Clickstream

### What it is

Monthly aggregated `(prev, curr, type, n)` tuples from Wikipedia request
logs. `type` is `link` (prev article links to curr), `other` (both are
articles but prev does not link to curr), or `external` (prev is a search
engine, other site, empty referrer, etc). Pairs with 10 or fewer observations
are removed; spider traffic is excluded. Source:
https://meta.wikimedia.org/wiki/Research:Wikipedia_clickstream

Format sample (measured, first rows of
https://dumps.wikimedia.org/other/clickstream/2026-08/clickstream-enwiki-2026-08.tsv.gz):

```
other-empty      Main_Page           external  190625915
Hayden_Panettiere  Wladimir_Klitschko  link   1732292
```

### Cadence and granularity

- **Monthly only** (published). Directory listing has 107 monthly folders,
  2017-11 through 2026-09, no gaps:
  https://dumps.wikimedia.org/other/clickstream/
- There is **no daily, weekly or hourly clickstream**. Any per-day or per-week
  number below is derived by dividing a month. (Hourly granularity exists only
  for plain pageviews, which carry no transition pairs.)
- Release lag is usually ~3 days after month end (e.g. 2026-09 posted
  2026-10-03), but there have been backfills: 2025-04..2025-09 all posted in
  early Oct 2025, and 2025-12..2026-04 all posted 2026-05-11 (published,
  folder timestamps on the listing above). Don't build anything that assumes
  a fixed lag.
- 2026-08 folder has 40 language editions (published,
  https://dumps.wikimedia.org/other/clickstream/2026-08/).

### Sizes (English)

`clickstream-enwiki-YYYY-MM.tsv.gz` Content-Length from the monthly folder
listings (published):

| Month | Compressed bytes |
|---|---|
| 2023-09 | 419,474,643 |
| 2024-09 | 496,868,177 |
| 2025-03 | 545,760,394 |
| 2025-09 | 509,228,675 |
| 2026-01 | 515,550,049 |
| 2026-07 | 492,902,361 |
| 2026-08 | 493,555,390 |
| 2026-09 | 479,161,129 |

Rows and uncompressed size (measured + derived): I range-fetched the first
15 MB of the 2026-08 gzip. It decompressed to 50,593,792 bytes and 1,073,572
rows (579,670 external, 480,108 link, 13,794 other). Scaling by bytes:

- Uncompressed: ~3.4x -> **~1.6-1.7 GB tsv per month** (derived).
- Rows: **~35M pairs per month** (derived). For comparison, the March 2016
  release had 25M pairs from 6.8B requests (published, meta page above).
- The type mix in the head of the file is not representative (the file is
  not uniformly shuffled), so I am not extrapolating the link/other/external
  split. Expect a large share to be `external` rows that we drop.

Derived per-period sizes (clickstream does not exist at these grains):

| Period | Compressed | Uncompressed | Pairs |
|---|---|---|---|
| per day (month / 30) | ~16 MB | ~55 MB | ~1.2M |
| per week | ~115 MB | ~390 MB | ~8M |
| per month (published) | 479-546 MB | ~1.6-1.8 GB | ~35M |
| per year (12 months) | ~6 GB | ~20 GB | ~420M rows, heavily overlapping pairs |

A year of files is mostly the same pairs repeated; unique pairs per year will
be far fewer than 420M.

### Article text options

| Source | Size | Freshness | Notes |
|---|---|---|---|
| enwiki `pages-articles-multistream.xml.bz2` | 26,917,225,724 B | 2026-10-08 | full wikitext, too big for a slice |
| enwiki `pages-articles.xml.bz2` | 25,800,511,704 B | 2026-10-08 | same, non-multistream |
| multistream index `.txt.bz2` | 285,227,194 B | 2026-10-08 | enables seeking to single articles |
| enwiki `pagelinks.sql.gz` | 7,167,161,183 B | 2026-10-08 | link graph (for the bias control) |
| HF `wikimedia/wikipedia` `20231101.en` | 11,630,929,031 B parquet, 41 shards, 6,407,814 rows | snapshot 2023-11-01, repo last modified 2024-01-09 | clean text, but ~3 years stale vs 2026 clicks |
| MediaWiki Action API | per request | live | best for a 5-20k subset |

Sources: https://dumps.wikimedia.org/enwiki/latest/ (listing sizes),
https://datasets-server.huggingface.co/size?dataset=wikimedia/wikipedia&config=20231101.en
and https://huggingface.co/api/datasets/wikimedia/wikipedia/tree/main/20231101.en
(HF sizes and rows), https://huggingface.co/api/datasets/wikimedia/wikipedia
(lastModified, license cc-by-sa-3.0 + gfdl).

API limits I verified against https://en.wikipedia.org/w/api.php:

- `prop=extracts&exintro=1&explaintext=1` returns up to 20 lead sections per
  request (`exlimit` max 20, from `action=paraminfo`).
- Whole-article plaintext extracts are capped at **1 per request** (the API
  warns: `"exlimit" was too large for a whole article extracts request,
  lowered to 1`). For full text use `prop=revisions&rvprop=content&rvslots=main`
  (wikitext, up to 50 titles per request) and strip markup locally.

### Licensing and access

- Clickstream: CC0 (published,
  https://dumps.wikimedia.org/other/clickstream/readme.html). No login.
- Article text: CC BY-SA (and GFDL for older text). Fine for internal
  experiments; attribution matters only if we republish text.
- dumps.wikimedia.org limits parallel connections per IP; download one file at
  a time. API: send a descriptive `User-Agent`, run requests serially.

### Label quality caveats

- **Link bias.** `link` rows can only exist where an editor already put a
  hyperlink. A "recommend from existing outlinks, ranked by popularity"
  baseline will beat any content model on these labels, and it tells us
  nothing about recommending pages that are not already linked. Report that
  baseline explicitly, and also score on `other` rows (transitions without a
  link: in-page search, edited-away links), which are less link-biased but
  much sparser.
- **Position and layout bias.** Clicks concentrate on links in the lead
  section and infobox, not on the most semantically related page.
- **Threshold censoring.** Pairs with n <= 10 are dropped, so the long tail of
  related-but-rare transitions is invisible; small topic clusters lose most of
  their labels. Pick a cluster with real traffic.
- **News and celebrity spikes.** Top pairs in 2026-08 were celebrity and
  movie navigation (sample above). A technical cluster avoids most of this.
- **Title drift.** Titles are as of that month; renames and redirects mean
  text from an older snapshot (e.g. HF 2023-11) will not join cleanly. Fetch
  text close to the click month, and resolve with `redirects=1`.
- **Scale mismatch.** Wikipedia readers are anonymous and huge in number; an
  internal wiki has few users and sparse logs. Treat absolute metric values
  as non-transferable; compare methods, not numbers.

## 2. Stack Exchange data dump

### What it is

One 7z archive per site containing Posts, PostLinks, PostHistory, Comments,
Votes, Users, Badges, Tags as XML. `PostLinks.LinkTypeId`: 1 = Linked
(`PostId` contains a link to `RelatedPostId`), 3 = Duplicate (published,
`sede-and-data-dump-schema.md` inside each archive; also
https://meta.stackexchange.com/questions/2677).

### Cadence, access history, and where to get it now

- Official dumps on archive.org item `stackexchange` were last refreshed in
  April 2024 (file mtimes 2024-04-06/07; published,
  https://archive.org/metadata/stackexchange).
- 2024-07-12: Stack Exchange announced dumps move off archive.org into the
  logged-in user settings page, behind terms that forbid using the file to
  train an LLM (https://wiki.archiveteam.org/index.php/Stack_Exchange,
  https://mjtsai.com/blog/?p=44090, https://heise.de/-9823083).
- Since then, a **community re-upload** to archive.org mirrors each official
  release. Items found via
  https://archive.org/advancedsearch.php?q=identifier%3Astackexchange_2*&fl%5B%5D=identifier&fl%5B%5D=publicdate&rows=50&output=json
  include `stackexchange_20240930`, `_20241231`, `_20250331`, `_20250630`
  (+`_rev2`), `_20250930`, `_20251231`, `_20260331`, `_20260630`. So the real
  cadence is **quarterly full snapshots** (data cut at quarter end, upload
  2-7 weeks later). There are **no incremental or daily dumps**.
- Latest: https://archive.org/details/stackexchange_20260630 (published
  2026-08-17), 98,538,193,873 bytes of .7z in total (published, metadata).
  Direct downloads work without login (`curl -sIL` on serverfault returned
  `HTTP/2 200`, `content-length: 907565303`).
- **Data poisoning warning**: the 2025-06-30 community item states "Stack
  Exchange has poisoned some of the data dumps with garbage data"
  (https://archive.org/details/stackexchange_20250630_rev2, pointing at
  https://meta.stackexchange.com/q/412018). Later items do not repeat the
  warning. The PostLinks files I parsed from 2026-06-30 looked clean, but
  spot-check Posts text before trusting a site.
- Compression changed: the 2026 archives use LZMA2 and Stack Overflow is now
  **one 68.9 GB archive** (no per-table split). The last per-table SO split is
  the 2024-04 official item (`stackoverflow.com-PostLinks.7z` 151,452,449 B,
  `stackoverflow.com-Posts.7z` 23,026,928,274 B; published,
  https://archive.org/metadata/stackexchange).

### Sizes (2026-06-30 snapshot)

Compressed sizes are archive.org metadata (published,
https://archive.org/metadata/stackexchange_20260630). Uncompressed XML sizes
come from reading each archive's 7z header via HTTP range requests (published
by the archive itself; ~1 MB fetched per site). PostLinks row counts are
measured by range-fetching and parsing only the PostLinks stream (0.7-2 MB
compressed each), except where marked derived.

| Site | .7z bytes | Posts.xml | PostLinks.xml | PostLinks rows (linked / dup) | Posts touched by a link |
|---|---|---|---|---|---|
| stackoverflow.com | 68,946,936,349 | 105,621,886,872 | 801,600,589 | ~6.5-7M (derived) | n/a |
| superuser.com | 1,400,358,958 | 1,713,797,505 | 10,741,044 | 90,744 (76,105 / 14,639) | 95,778 |
| serverfault.com | 907,565,303 | 1,244,120,295 | 4,183,700 | 35,562 (30,585 / 4,977) | 43,054 |
| unix.stackexchange.com | 759,322,794 | 1,031,447,566 | 8,021,410 | 68,607 (58,242 / 10,365) | 63,377 |
| softwareengineering.stackexchange.com | 377,945,136 | 440,112,757 | 1,790,284 | ~15k (derived) | n/a |
| devops.stackexchange.com | 18,189,978 | 23,720,160 | 41,770 | 374 (355 / 19) | 492 |

Derived row counts: measured PostLinks average 117-118 bytes per row on
superuser/serverfault/unix; SO ids are longer, so ~120-125 B/row.

Post counts:

- devops (measured, full 18 MB archive parsed): 5,589 questions, 7,791
  answers, 13,380 + 633 other posts.
- stackoverflow (published, live API on 2026-10-08,
  https://api.stackexchange.com/2.3/info?site=stackoverflow): 24,244,284
  questions, 36,100,573 answers.
- serverfault (same API, `site=serverfault`): 329,158 questions, 522,757
  answers.
- unix, superuser, softwareengineering: the API rate-limited me and the sites
  are behind a Cloudflare challenge. Derived from Posts.xml bytes at the
  ~1,460-1,750 B/post seen on serverfault/SO: unix ~0.6-0.7M posts
  (~0.25-0.3M questions), superuser ~1.0-1.2M posts, softwareengineering
  ~0.25-0.3M posts.

Label density (derived): on unix, 63k distinct posts touched by a link out of
~0.25-0.3M questions, so roughly 1 in 4-5 questions has any label; on devops
492 of 5,589 (~9%).

Growth per period (derived, comparing community snapshots):

- Whole network grew 91.5 MB of compressed data in one quarter (98,446,657,498
  B on 2026-03-31 to 98,538,193,873 B on 2026-06-30) -> ~1 MB/day.
- Stack Overflow archive grew 9.7 MB in that quarter (68,937,227,091 ->
  68,946,936,349).
- New labels per year collapse fast (measured, PostLinks CreationDate):

| Year | serverfault | superuser | unix |
|---|---|---|---|
| 2019 | 1,744 | 5,351 | 6,860 |
| 2022 | 1,078 | 3,515 | 4,450 |
| 2024 | 621 | 2,572 | 2,443 |
| 2025 | 316 | 1,621 | 1,418 |
| 2026 H1 | 56 | 550 | 378 |

That is ~4 new unix links per day in 2025 (derived). Per-day or per-week
dumps would be meaningless even if they existed; one snapshot is the dataset.

### Hugging Face mirrors (freshness)

None of the popular mirrors carry PostLinks and current data together:

- `mikex86/stackoverflow-posts`: 58,329,355 rows, 34,059,647,995 B parquet,
  last modified 2023-08-01, posts only.
- `flax-sentence-embeddings/stackexchange_xml`: raw per-site 7z, 2021.
- `HuggingFaceTB/stackexchange_2025_md`: 2025-03, markdown text (size query
  timed out).
- `mteb/cqadupstack-unix` (BEIR CQADupStack, 2015 data): 47,382-doc corpus,
  1,072 queries, 1,693 qrels, 26,346,288 B parquet. Ready-made duplicate
  retrieval benchmark; good 2-minute sanity check, but duplicates only and
  old.
- `mteb/StackOverflowDupQuestions`: 682,992 corpus rows, 22,839 queries.

Sources: https://huggingface.co/api/datasets?search=stackexchange&sort=downloads
and `https://datasets-server.huggingface.co/size?dataset=<id>` for each id.

### Licensing

Content is CC BY-SA 2.5 / 3.0 / 4.0 by contribution date (published,
`LICENSE.txt` and `license.txt` in the 2026-06-30 item). The official
in-profile download adds a "no LLM training" term that the CC license does
not; the community re-upload carries only the CC text. For an internal
retrieval experiment either is fine; do not ship SE text in a product without
attribution.

### Label quality caveats

- **Sparse and author-created.** A link exists only when someone pasted a URL
  or a moderator closed a duplicate. Most truly related questions are
  unlabeled, so recall@10 is a lower bound and false "misses" are common.
- **Duplicates are easy.** Duplicate pairs often share near-identical titles,
  so TF-IDF looks great on LinkTypeId=3. Report linked (1) and duplicate (3)
  separately; "linked" is closer to "what should I read next".
- **Directional but symmetric-ish.** `PostId` links to `RelatedPostId`; for a
  related-article task treat it as undirected.
- **Not navigation behavior.** No counts, no sequence, no user signal.
  It is relevance, not "what people actually read next".
- **Dangling ids.** Links can point to deleted or migrated posts; filter to
  ids present in Posts.
- **Q&A, not wiki.** Short question bodies plus answers, unlike long
  reference articles. Use title + question body + top answer as the document.

## 3. Laptop slice recipes

All paths below are a scratch area outside `labs/` (e.g.
`~/data/riot-proxy/`); the shared venv is used via `uv run` from the sandbox
root. Missing packages (`sentence-transformers`, `mwparserfromhell`) go in
with `uv add` at the sandbox root.

### 3a. Wikipedia: ~10k technical articles, one month of clicks

Target: < 1 GB on disk, ~15-25 min.

1. Download two months of clickstream (test month + an earlier month for
   tuning or a temporal check). ~480 MB each; one at a time.

   ```
   mkdir -p ~/data/riot-proxy/wiki && cd ~/data/riot-proxy/wiki
   B=https://dumps.wikimedia.org/other/clickstream
   curl -fLO $B/2026-09/clickstream-enwiki-2026-09.tsv.gz
   curl -fLO $B/2026-08/clickstream-enwiki-2026-08.tsv.gz   # optional
   ```

2. Keep only article-to-article rows (drop `external`), write parquet, then
   delete the gz if disk is tight. Polars `read_csv` with
   `separator="\t", has_header=False, quote_char=None` and column names
   `prev, curr, type, n`; filter `type in ("link", "other")`. Expected output:
   on the order of 100-300 MB parquet for all of enwiki (derived; the
   link/other share is not known until the full file is read).

3. Define the topic cluster independently of the clicks, from categories,
   so the candidate set is not chosen by the labels:

   ```
   https://en.wikipedia.org/w/api.php?action=query&list=categorymembers
     &cmtitle=Category:Unix&cmtype=page|subcat&cmlimit=500
     &format=json&formatversion=2
   ```

   BFS to depth 2-3 from ~5-10 roots (e.g. `Category:Unix`,
   `Category:Computer_networking`, `Category:Software_engineering`,
   `Category:Cloud_computing`, `Category:Database_management_systems`).
   `Category:Unix` alone has 63 members, 13 of them subcategories (measured).
   Stop when the article set reaches ~10-20k; cap depth to avoid category
   drift. Normalize titles to underscores to match clickstream.
   Fallback if categories drift: seed 50 hand-picked articles and expand 2 hops
   over `link` rows with `n >= 50`, keeping the top 10k by inbound clicks
   (simpler, but the candidate set is now label-selected; note it).

4. Labels: keep clickstream rows where both `prev` and `curr` are in the
   cluster. Relevance for nDCG = `n` (or log(1+n)). Keep `type` so metrics
   can be cut by `link` vs `other`. Expected: tens of thousands to low
   hundreds of thousands of pairs, < 10 MB (derived, depends on cluster
   traffic).

5. Text: lead sections are enough for a first baseline and are cheap:
   `prop=extracts&exintro=1&explaintext=1&redirects=1&titles=A|B|...` with 20
   titles per call -> 500 calls for 10k articles, ~5-10 min serial, ~15-30 MB
   (derived at ~1.5-3 KB per lead). For full text use
   `prop=revisions&rvprop=content&rvslots=main` (50 titles/call, 200 calls),
   strip with `mwparserfromhell`; expect ~200-300 MB wikitext for 10k
   technical articles (derived, ~20-30 KB each).

6. Evaluation split: for each source article, hold out its top targets.
   Cleanest options: (a) split by source article 80/20; (b) temporal: build
   any tuned component on 2026-08, test on 2026-09 pairs. Score recall@10 and
   nDCG@10, candidate pool = the cluster minus the source.

7. Baselines to report side by side: popularity (global inbound clicks),
   **outlink-popularity** (rank the source's existing outlinks by inbound
   clicks; needs the source's outlinks, available from `link` rows or
   `prop=links`), TF-IDF cosine kNN, sentence-embedding kNN
   (`all-MiniLM-L6-v2`, 10k x 384 float32 = ~15 MB). The outlink baseline is
   the honest ceiling check for link bias.

Expected total: ~480-960 MB of gz (deletable after step 2) + < 300 MB of
parquet/text/embeddings.

### 3b. Stack Exchange: unix.stackexchange.com, Posts + PostLinks only

Target: ~240 MB download, < 1.5 GB peak disk, ~10-15 min.

The 2026 archives store each table (or a few tables) as separate LZMA2
streams, so you can range-fetch just the stream you need instead of the whole
7z. For unix, PostLinks and Posts sit in the same stream (folder 2, bytes
454,415,325-690,709,248, 236,293,924 B compressed, together with Tags). For
serverfault, PostLinks is its own 668,831 B stream and Posts its own
293,209,294 B stream. Measured with the helper below.

1. Helper (keep it in the scratch area, not in `labs/`). It reads the 7z
   header via range requests, finds the stream holding the table, streams
   that byte range through raw LZMA2, and writes only that table's bytes.
   Uses `py7zr` (already in the shared venv) for header parsing and the
   private `lzma._decode_filter_properties`.

   ```python
   """se_stream.py <site> <Table.xml> <out>  (SE_DUMP env overrides dump id)"""
   import lzma, os, struct, subprocess, sys
   import py7zr

   DUMP = os.environ.get("SE_DUMP", "stackexchange_20260630")
   site, table, out = sys.argv[1:4]
   url = f"https://archive.org/download/{DUMP}/{DUMP}/{site}.7z"

   def rng(a, b):
       return subprocess.run(["curl", "-sL", "-r", f"{a}-{b}", url],
                             capture_output=True, check=True).stdout

   sh = rng(0, 31)
   off, size = struct.unpack("<QQ", sh[12:28])
   end = 32 + off + size
   ts = max(32, end - 1_000_000)
   tmp = out + ".hdr.7z"
   with open(tmp, "wb") as f:      # sparse file: start header + tail only
       f.write(sh); f.seek(ts); f.write(rng(ts, end - 1))
   z = py7zr.SevenZipFile(tmp); mi = z.header.main_streams; os.remove(tmp)

   names = [f.filename for f in z.files]
   counts = mi.substreamsinfo.num_unpackstreams_folders
   fmap = [fi for fi, c in enumerate(counts) for _ in range(c)]
   fi = fmap[names.index(table)]
   k = names.index(table) - fmap.index(fi)
   subs = ([s for j, s in enumerate(mi.substreamsinfo.unpacksizes)
            if fmap[j] == fi] if counts[fi] > 1
           else [mi.unpackinfo.folders[fi].unpacksizes[-1]])
   skip, want = sum(subs[:k]), subs[k]
   coder = mi.unpackinfo.folders[fi].coders[0]
   assert coder["method"] == b"\x21"  # LZMA2
   start = 32 + mi.packinfo.packpos + sum(mi.packinfo.packsizes[:fi])
   n = mi.packinfo.packsizes[fi]
   filt = lzma._decode_filter_properties(lzma.FILTER_LZMA2,
                                         coder["properties"])
   dec = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=[filt])
   p = subprocess.Popen(["curl", "-sL", "-r", f"{start}-{start + n - 1}",
                         url], stdout=subprocess.PIPE)
   pos = got = 0
   with open(out, "wb") as f:
       while got < want and (chunk := p.stdout.read(1 << 20)):
           d = dec.decompress(chunk)
           a, b = max(0, skip - pos), min(len(d), skip + want - pos)
           if b > a:
               f.write(d[a:b]); got += b - a
           pos += len(d)
   p.kill()
   ```

2. Fetch the two tables:

   ```
   mkdir -p ~/data/riot-proxy/se && cd ~/data/riot-proxy/se
   uv run --project ~/dev/sandbox python se_stream.py \
     unix.stackexchange.com PostLinks.xml PostLinks.xml   # 8,021,410 B
   uv run --project ~/dev/sandbox python se_stream.py \
     unix.stackexchange.com Posts.xml Posts.xml           # 1,031,447,566 B
   ```

   Alternative without the helper: download the whole archive (759,322,794
   B) from
   https://archive.org/download/stackexchange_20260630/stackexchange_20260630/unix.stackexchange.com.7z
   and extract with `py7zr` (`SevenZipFile.extract(targets=[...])`), which is
   ~3x the download.

3. Parse Posts.xml with `xml.etree.ElementTree.iterparse`, clearing elements
   as you go. Keep questions (`PostTypeId="1"`): `Id, Title, Body, Tags,
   CreationDate, Score, ViewCount, AcceptedAnswerId`; optionally join the
   accepted answer body. Strip HTML (`lxml.html` or a regex on `<[^>]+>` plus
   `html.unescape`). Write parquet; delete Posts.xml. Expected ~0.25-0.3M
   questions, ~150-300 MB parquet (derived).

4. Labels: PostLinks rows where both ids are questions in the table; make
   them undirected; keep `LinkTypeId` and `CreationDate`. Expect somewhat
   fewer than the 68,607 raw rows after filtering dangling ids.

5. Corpus subset: all questions touched by a surviving link (~60k) plus a
   random sample of unlinked questions as distractors, up to ~100k docs. TF-IDF
   on 100k docs and MiniLM embeddings (100k x 384 float32 = ~150 MB, ~10-20 min
   on a laptop CPU) both fit.

6. Split: temporal by link `CreationDate`. E.g. test = links created on or
   after 2024-01-01 (2,443 + 1,418 + 378 = 4,239 raw links), dev = 2022-2023.
   Report linked (1) and duplicate (3) separately. Also run the same code on
   `mteb/cqadupstack-unix` (26 MB) first as a sanity check against published
   BEIR numbers.

Swap to serverfault by changing the site name: PostLinks is a separate
668,831 B stream and Posts a separate 293,209,294 B stream (measured).

## 4. Recommendation

Use **Wikipedia Clickstream first**, on a category-defined ~10k-article
technical cluster with 2026-09 clicks and API lead-section text.

- It is behavioral "read A, then read B" data, the exact shape of the
  internal-wiki target, with graded relevance (`n`) for nDCG.
- Labels are dense: one month gives millions of article pairs, so even a
  10k-article cluster yields enough held-out pairs for stable metrics.
- Clicks are CC0, no login, monthly and fresh; the slice is a single 480 MB
  download plus a few hundred API calls.
- Its main flaw, link bias, is measurable: always report the outlink-
  popularity baseline and the `other`-type slice next to TF-IDF/embeddings.

Then run **Stack Exchange unix (or serverfault)** as the second corpus. Its
labels are sparse and editorial rather than behavioral, but they are much
less tied to existing hyperlinks and the text is closer to internal tech
docs/Q&A. The range-fetch trick keeps it to ~240 MB of download (unix) or
~295 MB (serverfault). Skip stackoverflow.com for a laptop: PostLinks alone
is ~800 MB uncompressed and Posts is 105.6 GB inside a single 68.9 GB archive.
