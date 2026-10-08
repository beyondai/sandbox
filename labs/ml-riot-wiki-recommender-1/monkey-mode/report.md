# Monkey-mode baseline: Riot wiki "related article" recommender

Proxy run on Wikipedia Clickstream (enwiki, 2026-09). Script:
`monkey-mode/baseline.py`. Raw metrics: `monkey-mode/metrics.json`. Full run
log: `monkey-mode/run.log`. One full run takes about 90 s on the laptop.

## Requirements

- **Task** (answered-by-user): given the article a reader is on (A), rank
  the next articles (C) they will open. Source = enwiki clickstream 2026-09,
  all articles. "One week" of history = Binomial(n, 7/30) thinning of each
  monthly pair count into history and truth.
- **Primary metric** (answered-by-user, recommended option): nDCG@10, plus
  recall@10, hit@10 and catalog coverage, overall and per traffic bucket
  (cold / tail / torso / head).
- **Success bar** (answered-by-user): the ML reranker beats the tuned click
  baseline B1 by at least +5% relative nDCG@10 overall, or clearly wins
  (bootstrap 95% CI excludes 0) on both the tail and cold buckets.
- **ML challenger** (answered-by-user): click-graph reranker, no text. Text
  similarity is a written plan only (Suggested Next Steps).
- **Two models, not one** (answered-by-user): the user asked for a click
  baseline and an ML challenger, which overrides the skill's one-model fast
  default.
- **Eval sample** (self-inferred, stated per the plan): **57,760 eval query
  articles, 2.73% of the 2,113,241 source articles in the full file**, over
  the full universe of 3,281,519 articles (no article is dropped). Train
  uses another 115,521 disjoint sources (5.47%).
- **Bucket thresholds, query counts, seed 42, the HGB model and its
  settings** (self-inferred, from the approved plan).
- **"Overall" = population-weighted mean of bucket means** (self-inferred).
  Buckets are over-sampled in eval (5,000 cold and 5,000 head minimum), so
  each bucket mean is reweighted by its share of all 2.11M sources.
- **Reranker variants beyond the plan** (self-inferred, added after the
  plan's version underperformed): a graded-label reranker, a B1/reranker
  hybrid, and a novel-pair diagnostic slice. The plan's binary reranker is
  still the primary challenger and is reported first.

## Input

- **File:** `data/wikipedia-clickstream/clickstream-enwiki-2026-09.tsv.gz`
  (479,161,129 bytes, CC0), downloaded from
  https://dumps.wikimedia.org/other/clickstream/2026-09/. It is
  gitignored, as are the intermediates written next to it
  (`pairs_thinned_seed42.parquet`, 155 MB; `titles.parquet`, 36 MB).
- **Rows:** 33,553,254 rows and 5.70B clicks.
  - By type: 21,241,303 `link`, 780,652 `other`, 11,531,299 `external`.
  - After keeping `link`/`other`, dropping self pairs and dropping
    `Main_Page` as a source: **21,767,189 rows and 2,015,385,749 clicks**.
- **Catalog:** 3,281,519 distinct articles (all of them kept).
- **Thinning:** total h / total n = **0.23335** (target 7/30 = 0.23333).
  - History: 21,440,717 pairs with h > 0.
  - Truth: 21,767,189 pairs with t > 0. Every pair keeps some truth, because
    n >= 11 upstream.
- **Sources with truth:** 2,113,241, by history out-clicks:
  - cold (0): 16,745, which is 0.79%;
  - tail (1-50): 1,429,816, which is 67.7%;
  - torso (51-1000): 588,763, which is 27.9%;
  - head (>1000): 77,917, which is 3.7%.
- **Query samples:** disjoint, stratified by bucket, seed 42.

  ```
  split       cold   tail    torso   head   total
  eval        5,000  33,830  13,930  5,000  57,760   (2.73% of sources)
  train-fit   8,956  60,969  25,078  8,966  103,969
  val (B1)    1,044   6,691   2,783  1,034  11,552   (10% of train)
  ```

## Design

### How training data and ground truth are built

The clickstream is a monthly total per (A, C) pair, with no timestamps. To
get a "first week vs rest of month" split, every pair's count n is split
click by click: each click lands in history with probability 7/30, so
`h ~ Binomial(n, 7/30)` and `t = n - h`.

- **History (h)** is the only input anything may use. That covers B0, B1,
  candidate generation and all reranker features.
- **Truth (t)** is where readers went in the rest of the month. For an eval
  query A, every C with t > 0 is relevant, with graded gain log1p(t).
- **Queries** are source articles, split by page. No page is both a train
  and an eval query (asserted).
- **Reranker labels.** For each train query, the candidates get history
  features. Truth is then joined on (A, C), giving the label `t > 0`, or
  `log1p(t)` for the graded variant.

**Worked example.** Source A = `'Mamohato_Bereng_Seeiso` (an eval query in
the torso bucket). It has 6 article targets, and H(A) = 54 history
out-clicks:

```
target C                    type   n (month)   h (history)   t (truth)   B1 rank
Prince_Seeiso_of_Lesotho    link   66          15            51          1
Letsie_III                  link   51          13            38          2 (tie, more popular)
Moshoeshoe_II_of_Lesotho    link   62          13            49          3 (tie)
Lesotho                     link   18           6            12          4
Mafeteng_District           link   13           4             9          5
'Masenate_Mohato_Seeiso     link   14           3            11          6
(B0 backfill x4)            -      -            -             0          7-10
```

How to read the example:

- The baselines and features only ever see the h column.
- The t column is the answer key.
- B1 ranks by h. It gets the order nearly right but swaps two pairs:
  - Letsie_III and Moshoeshoe_II tie at h = 13, and the popularity
    tie-break picks the wrong one;
  - Mafeteng_District (h = 4) is placed above 'Masenate_Mohato_Seeiso
    (h = 3), but their truth order is 11 > 9.
- The result is nDCG@10 = 0.9966 for this query. A reranker can only beat
  that by fixing small, noisy orderings, or by finding targets the history
  never showed.

**Caveat: a random split, not a time split.** Binomial thinning treats
every click as an independent draw from the same monthly distribution, so h
and t have the same expected ranking. That flatters any count-based method.
On real dated logs, history and future differ through trends, news spikes
and new pages, which is exactly where B1 would degrade. Separately,
Wikimedia removed pairs with n <= 10 upstream, so truth misses the rare
tail.

### Models

- **B0 popularity.** The top articles by history in-clicks, excluding A.
- **B1 co-visitation.** Rank C by h(A, C), backfilled with B0. Cold queries
  have no out-edges, so B1 falls back to B0 alone (asserted equal).
  - **Noise handling** was tuned on the 11,552 val queries as a 5 x 5 grid
    of `min_h in {1,2,3,5,10}` x `alpha in {0,1,5,20,100}`.
  - The score is `(h + alpha * P_pop(C)) / (H(A) + alpha)`.
- **Reranker (plan version).** It has three steps:
  - **Candidates per A**, from history only:
    - B1 top 50 out-edges;
    - 2-hop paths, top 50 by sum over B of P(B|A) * P(C|B), with each hop
      capped at its top 20;
    - top 20 reverse edges (pages that send clicks to A);
    - B0 top 20.
  - **Features** (10): h(A,C), P(C|A), B1 rank, 2-hop score, reverse
    h(C,A), C in-clicks, C out-clicks, A out-clicks, pair type (link /
    other / missing), and the number of generators that produced C.
  - **Model:** sklearn `HistGradientBoostingClassifier` on the binary label
    t > 0, ranking by predicted probability. It has 63 leaves, learning rate
    0.1, early stopping (107 iterations) and 6.0M training rows. The rows
    are a uniform 99.7% subsample of 6,017,139, with positive rate 17.4%.
- **Reranker_graded (addition).** The same candidates and features, with
  `HistGradientBoostingRegressor` trained on log1p(t) (0 for non-truth),
  run for 208 iterations. This was added because nDCG rewards ordering by
  click volume, and the binary label cannot express that (see Learnings).
- **Hybrid (addition).** B1 for sources with any history, the plan's
  reranker for cold sources.

### Metrics

- **nDCG@10:** gain log1p(t), with IDCG from the query's top 10 truth
  targets.
- **recall@10:** hits / all relevant targets (set-based).
- **recall_w@10:** truth clicks hit / all truth clicks (click-weighted).
- **hit@10:** at least one relevant target in the top 10.
- **coverage:** distinct recommended articles / 3,281,519.
- **Bootstrap CIs:** 1,000 resamples of queries within each bucket, seed
  42. The overall CI combines the bucket resamples with the population
  weights.

Fast defaults applied: no cleaning beyond the filter, no scaling (trees),
no text, one training run per model.

## Implementation

Real code that ran (excerpts of `baseline.py`; the full file is 687 lines).
Run from the sandbox root:

```
uv run python3 labs/ml-riot-wiki-recommender-1/monkey-mode/baseline.py
```

Thinning, in file order, with seed 42:

```python
rng = np.random.default_rng(SEED)
n = df["n"].to_numpy()
h = rng.binomial(n, P_HIST).astype(np.int64)
df = df.with_columns(h=pl.Series(h), t=pl.Series(n - h))
```

History-only object. Its constructor asserts there is no truth column:

```python
class History:
    def __init__(self, hist: pl.DataFrame):
        assert set(hist.columns) == {"src", "dst", "type", "h"}, hist.columns
        assert "t" not in hist.columns
```

B1 with min_h and popularity smoothing:

```python
    def b1(self, q, min_h=1, alpha=0.0, k=K):
        e = (
            self.edges.join(q.select(src="q"), on="src")
            .filter(pl.col("h") >= min_h)
            .join(self.in_h, on="dst", how="left")
            .with_columns(score=pl.col("h") + alpha * pl.col("in_h") / self.in_h["in_h"].sum())
            .pipe(topk, "src", ["score", "dst"], [True, False], k)
            .select(q="src", item="dst", r="rank")
        )
        back = self.b0(q, k).select("q", "item", r=pl.col("rank") + 10_000)
        return (pl.concat([e, back]).group_by(["q", "item"]).agg(pl.col("r").min())
                .pipe(topk, "q", ["r"], [False], k).select("q", "item", "rank"))
```

2-hop and reverse-edge candidates:

```python
        hop1 = topk(a_edges, "src", ["h", "dst"], [True, False], 20).select(
            q="src", b="dst", p1="p")
        hop2 = (self.edges.join(hop1.select(src="b").unique(), on="src")
            .join(self.out_h, on="src").with_columns(p2=pl.col("h") / pl.col("H"))
            .pipe(topk, "src", ["h", "dst"], [True, False], 20)
            .select(b="src", item="dst", p2="p2"))
        twohop = (hop1.join(hop2, on="b").filter(pl.col("item") != pl.col("q"))
            .group_by(["q", "item"]).agg(twohop=(pl.col("p1") * pl.col("p2")).sum()))
        rev_all = self.edges.join(q.select(dst="q"), on="dst").select(
            q="dst", item="src", rev_h="h")
```

Per-query metrics:

```python
    hits = (recs.join(tq, on=["q", "item"], how="left")
        .with_columns(pl.col("gain").fill_null(0), pl.col("t").fill_null(0))
        .group_by("q")
        .agg(dcg=(pl.col("gain") / (pl.col("rank") + 1).log(2)).sum(),
             n_hit=(pl.col("t") > 0).sum(), t_hit=pl.col("t").sum()))
    # ndcg = dcg / idcg, recall = n_hit / n_rel, recall_w = t_hit / t_sum
```

### Verification output (from `run.log`)

```
[    4.7s] raw rows=33,553,254 by type={'external': 11531299, 'link': 21241303, 'other': 780652}
[    4.9s] filtered rows=21,767,189 clicks=2,015,385,749
[    6.2s] thinning: sum(h)/sum(n) = 0.23335 (target 0.23333)
[   13.9s] assert ok: train (115,521) and eval (57,760) query sets are disjoint
[   22.9s] assert ok: features built from history only (columns: ['b1_rank', 'h_ac',
          'in_c', 'item', 'n_sources', 'out_a', 'out_c', 'p_c_given_a', 'pair_type',
          'q', 'rev_h', 'twohop']); truth joined afterwards
[   73.7s] assert ok: B1 == B0 on 5,000 cold eval queries
```

Reproducibility: the full pipeline ran twice with seed 42 and wrote the
`metrics.json` files, which were compared programmatically:

```
runtimes s: 89.0 91.4
run1 == run2 (all metrics, rounded to 1e-10): True
final run == previous run (seed 42): True
```

## Results

### B1 noise sweep (val, 11,552 queries, overall nDCG@10)

```
min_h  alpha=0   alpha=1   alpha=5   alpha=20  alpha=100  recall@10  hit@10
1      0.973468  0.973566  0.973566  0.973566  0.973566   0.8655     0.9921
2      0.916605  0.916699  0.916699  0.916699  0.916699   0.7953     0.9596
3      0.819696  0.819773  0.819773  0.819773  0.819773   0.6762     0.9022
5      0.598485  0.598521  0.598521  0.598521  0.598521   0.4222     0.7423
10     0.324799  0.324808  0.324808  0.324808  0.324808   0.1634     0.4719
```

Best: **min_h = 1, alpha = 1** (alpha >= 1 all tie, and the smallest wins).

- Raising min_h only throws away true signal.
- Alpha only acts as a popularity tie-break among equal h, because max
  P_pop = 2.3e-3 means alpha * P_pop < 1 for every alpha tested. Its whole
  effect is +0.0001 nDCG.

### Eval metrics, per bucket (57,760 queries)

```
model            bucket   nDCG@10  recall@10  recall_w@10  hit@10  coverage
B0               overall  0.0071   0.0021     0.0012       0.0528  0.0000
B0               cold     0.0014   0.0014     0.0014       0.0014  0.0000
B0               tail     0.0012   0.0010     0.0009       0.0027  0.0000
B0               torso    0.0117   0.0036     0.0016       0.0883  0.0000
B0               head     0.0813   0.0116     0.0036       0.7154  0.0000
B1 (tuned)       overall  0.9737   0.8643     0.9255       0.9921  0.0668
B1 (tuned)       cold     0.0014   0.0014     0.0014       0.0014  0.0000
B1 (tuned)       tail     0.9809   0.9846     0.9863       1.0000  0.0266
B1 (tuned)       torso    0.9808   0.6869     0.8408       1.0000  0.0339
B1 (tuned)       head     0.9970   0.1840     0.6489       1.0000  0.0135
Reranker (plan)  overall  0.9169   0.8702     0.8590       0.9944  0.1105
Reranker (plan)  cold     0.2575   0.2981     0.2982       0.2998  0.0027
Reranker (plan)  tail     0.9767   0.9896     0.9905       0.9999  0.0724
Reranker (plan)  torso    0.8288   0.6876     0.6487       1.0000  0.0369
Reranker (plan)  head     0.6280   0.1840     0.1558       1.0000  0.0125
Reranker_graded  overall  0.9789   0.8704     0.9315       0.9945  0.1092
Reranker_graded  cold     0.2578   0.2981     0.2982       0.2998  0.0027
Reranker_graded  tail     0.9851   0.9899     0.9911       1.0000  0.0715
Reranker_graded  torso    0.9821   0.6875     0.8423       1.0000  0.0373
Reranker_graded  head     0.9967   0.1840     0.6485       1.0000  0.0135
Hybrid           overall  0.9757   0.8667     0.9279       0.9945  0.0689
Hybrid           cold     0.2575   0.2981     0.2982       0.2998  0.0027
Hybrid           (tail, torso and head are identical to B1)
```

Notes on the table:

- Overall coverage is over all eval queries; a bucket's coverage is over
  that bucket's queries only. B0 recommends only about 11 distinct
  articles in total, which rounds to 0.0000 of the catalog.
- Untuned B1 (min_h = 1, alpha = 0) scores 0.9736 overall nDCG@10.
- Candidate click-recall (the reranker's ceiling) is cold 0.298, tail 0.993,
  torso 0.992 and head 0.929.

### Bootstrap 95% CIs, nDCG@10 delta vs tuned B1

```
model - B1        bucket   delta     95% CI               relative
Reranker (plan)   overall  -0.0567   [-0.0574, -0.0561]   -5.83% [-5.89, -5.76]
Reranker (plan)   cold     +0.2561   [+0.2451, +0.2667]   B1 = 0.0014
Reranker (plan)   tail     -0.0042   [-0.0046, -0.0037]   -0.42%
Reranker (plan)   torso    -0.1520   [-0.1539, -0.1499]   -15.5%
Reranker (plan)   head     -0.3690   [-0.3720, -0.3660]   -37.0%
Reranker_graded   overall  +0.0052   [+0.0050, +0.0055]   +0.54% [+0.51, +0.57]
Reranker_graded   cold     +0.2564   [+0.2452, +0.2673]   B1 = 0.0014
Reranker_graded   tail     +0.0042   [+0.0039, +0.0046]   +0.43%
Reranker_graded   torso    +0.0013   [+0.0011, +0.0014]   +0.13%
Reranker_graded   head     -0.0003   [-0.0004, -0.0003]   -0.03%
Hybrid            overall  +0.0020   [+0.0019, +0.0021]   +0.21% [+0.20, +0.22]
Hybrid            cold     +0.2561   [+0.2451, +0.2667]   B1 = 0.0014
```

### Novel-pair slice (diagnostic)

Truth here is restricted to pairs with h = 0: targets that history never
showed from A. These hold only 0.24% of eval truth clicks. The slice covers
5,000 cold, 1,815 tail, 3,051 torso and 2,426 head queries.

```
model             cold    tail    torso   head    (nDCG@10)
B0                0.0014  0.0006  0.0097  0.0142
B1 (tuned)        0.0014  0.0002  0.0005  0.0000
Reranker (plan)   0.2575  0.1310  0.0068  0.0000
Reranker_graded   0.2578  0.1338  0.0067  0.0000
```

On tail queries, Reranker_graded reaches recall@10 0.315 on these unseen
targets, against 0.0006 for B1.

### Permutation importance (nDCG@10 drop, 5,000 eval queries)

```
Reranker (plan), base 0.9161       Reranker_graded, base 0.9783
h_ac          0.5587               h_ac          0.6150
p_c_given_a   0.0533               b1_rank       0.0068
b1_rank       0.0215               pair_type     0.0045
in_c          0.0006               rev_h         0.0033
twohop        0.0003               out_a         0.0009
n_sources     0.0000               out_c         0.0008
out_c        -0.0002               p_c_given_a   0.0006
out_a        -0.0097               n_sources     0.0004
rev_h        -0.0105               twohop        0.0003
pair_type    -0.0172               in_c          0.0000
```

### Verdict vs the success bar

- **+5% relative nDCG@10 overall: not reachable on this proxy.** Tuned B1
  is already at 0.9737, so even a perfect ranker (1.0) is only +2.7%.
- **Reranker (plan version, binary label): FAILS.**
  - It is -5.8% overall and loses on tail (-0.0042, CI excludes 0).
  - It wins only on cold (+0.256).
- **Reranker_graded (addition): PASSES on the second clause.**
  - It clearly wins on both tail (+0.0042, CI [+0.0039, +0.0046]) and cold
    (+0.256, CI [+0.245, +0.267]).
  - It is +0.54% overall, with a CI excluding 0.
  - The tail win is statistically clear but tiny in absolute terms.
  - The cold win is large, and is the only practically meaningful one.
- **Bottom line:** on warm pages, click co-visitation is near the ceiling of
  this proxy. The ML value is entirely in cold-start and discovery (the
  novel-pair slice), which is what Riot's day one looks like.

## Learnings

- **The proxy saturates.** Binomial thinning makes history and truth two
  samples of the same distribution, so ranking by h nearly reproduces the
  ranking by t.
  - B1 gets nDCG@10 0.97-0.997 on all warm buckets.
  - This is a property of the split, not evidence that co-visitation is
    this good on real future traffic.
  - Absolute numbers should not be carried to Riot. Compare methods only.
- **The plan's binary label was the main design flaw.**
  - Every history edge has n >= 11, so almost every candidate that is a
    history out-edge has t > 0. P(t > 0) is near 1 for all of them, and the
    classifier cannot order them by volume.
  - Head-bucket nDCG collapsed from 0.997 to 0.628, while recall@10 stayed
    identical (0.184).
  - Switching to a log1p(t) regression target fixed it with no other
    change.
  - Lesson: for graded nDCG, train on the graded target (or use LambdaMART).
- **The min_h / alpha sweep was nearly a no-op.**
  - Upstream already drops n <= 10, so there are no junk pairs left to
    filter, and min_h > 1 only deletes signal.
  - Alpha is bounded by P_pop <= 2.3e-3, so it never moves an edge past
    another edge with a different h; it only breaks ties.
- **Cold start is almost entirely reverse edges.**
  - Cold pages have no out-clicks but often receive clicks. Pages that link
    in are good recommendations, with nDCG 0.258 against 0.0014 for B0.
  - The candidate ceiling for cold is 0.298 click-recall, so better cold
    results need a new candidate source (text), not a better ranker.
- **Feature use.**
  - h_ac dominates. In the binary model, permuting pair_type, rev_h or out_a
    raises nDCG, a sign it learned shortcuts toward "any edge = positive".
  - The graded model uses them sensibly but lightly.
  - 2-hop adds almost nothing on warm pages here.
- **Coverage.** The rerankers recommend 1.6x more distinct articles than B1
  (0.109 vs 0.067 of the catalog), mostly via reverse and 2-hop candidates
  on tail pages.
- **Data gotchas.**
  - Titles containing `"` are CSV-quoted in the raw TSV. Reading with
    `quote_char=None` keeps them verbatim and consistent across prev/curr,
    but they look odd (the worked example was chosen to avoid one).
  - Tie order from parallel polars group_by sums gave about 1e-16 float
    noise, which flipped the best-alpha pick between runs. It is fixed by
    rounding before argmax, with ties going to the simplest config.
- **Environment.** The shared env (polars 1.44.2, sklearn 1.9.1, numpy
  1.26.4) had everything. No packages were added. The whole run took about
  90 s, well under budget, so no sample shrinking was needed.

## Suggested Next Steps

- **Fix the eval before trusting margins.** Use two real months as a
  temporal split: history = 2026-08, truth = 2026-09.
  - This shows how much B1 degrades with real drift, and gives a fairer
    challenger test than thinning.
  - It is cheap: one more 480 MB download, with the same script.
- **Report the `other`-type slice.** These are transitions without an
  existing hyperlink, the part less biased by links. Add it alongside the
  novel-pair slice.
- **Use the graded (or LambdaMART-style) reranker as the V1 model class.**
  Keep the hybrid's lesson: route cold pages to the non-co-visitation
  generators.
- **Text similarity (written plan only, not built):**
  - **Text source.**
    - Option 1: HF `wikimedia/wikipedia` 20231101.en (11.6 GB parquet, 6.4M
      rows). It needs a title join through redirects and normalization,
      because the 2023 snapshot is stale against 2026 click titles.
    - Option 2: the current enwiki XML dump (about 27 GB bz2), or the
      MediaWiki API for a subset (lead extracts, 20 per request).
  - **Document and index.**
    - Document = title + lead section.
    - TF-IDF (sublinear tf, unigrams + bigrams) first. MiniLM sentence
      embeddings second, which needs `uv add sentence-transformers` at the
      sandbox root.
    - An ANN index (hnswlib or FAISS HNSW) over about 6.8M pages; 384-dim
      float32 is about 10 GB, so use a subset or PQ on the laptop.
  - **Uses.**
    - (a) A new candidate generator for cold and tail queries. Cold
      candidate recall is capped at 0.298 today.
    - (b) A `cos(A, C)` feature on every candidate in the reranker.
    - (c) The main lever for Riot. On day one every internal wiki page is
      cold, so text kNN is the V0 there, and click features take over as
      logs accumulate.
  - **Eval:** the same script, comparing cold and novel-pair slice nDCG@10
    with and without the text generator.
- **Carry to the regular flow:**
  - The PRD/design should state that a co-visitation baseline will look
    near-perfect on mature pages.
  - Success for Riot should be measured on cold and new pages, plus a
    temporal split, not on overall nDCG.
