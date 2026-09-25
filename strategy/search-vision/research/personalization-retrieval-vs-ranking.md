# Where does personalization happen: retrieval or ranking?

Researched 2026-09-25. Every claim below is from the paper's abstract or
full text as fetched, or from the company's own engineering blog. Company
names are given only where the source states them.

## Summary

- Both. No mature system we found personalizes only at retrieval, and the
  ones that report the largest wins personalize retrieval too.
- The industry splits:
  - **JD, Taobao/Tmall, Etsy, Facebook, Kuaishou:** personalize retrieval
    (as one retrieval channel, or end to end).
  - **Walmart, Instacart:** run non-personalized embedding retrieval and
    personalize in ranking.
- The reason to personalize retrieval is recall on **broad queries**. When
  a query matches ~100k items, a non-personalized top-500 is close to
  arbitrary for this guest, and no reranker can recover what was never
  retrieved. For **specific queries** the match set is small enough for
  ranking to cover it, and retrieval personalization adds little.
- The main risk is relevance drift: personalized candidates can drift off
  the query. Production systems pair personalized retrieval with a
  non-personalized lexical/semantic backbone and a relevance filter.
- The frontier (2025-26, Chinese platforms) is generative retrieval that
  merges retrieval and ranking, with personalization throughout. It has
  real online wins, but it is a large rebuild and its relevance guarantees
  are unproven for US retail.

## Personalized at retrieval (production, online A/B)

- **Facebook Search, KDD 2020** (Huang et al., arXiv 2006.11632).
  "the search intent does not only depend on query text but is also
  heavily influenced by the user who is issuing the query". The query side
  includes "searcher location and their social connections". EBR runs as
  hybrid retrieval inside the inverted index (an `(nn)` operator). Lesson:
  existing rankers under-rank the new EBR results, so they added the
  embedding similarity as a ranking feature.
  https://arxiv.org/abs/2006.11632
- **JD.com DPSR, SIGIR 2020** (Zhang et al., arXiv 2006.02282). Names
  "how to retrieve items that are more personalized to different users for
  the same search query" as one of the two core problems. Result: +1.29%
  conversion rate overall, +10.03% on long-tail queries. In production since
  2019.
  https://arxiv.org/abs/2006.02282
- **Taobao MGDSPR, KDD 2021** (Li et al., arXiv 2106.09297). The goal is
  retrieval "while preserving personalized user characteristics". Deployed
  as one channel of Taobao's multi-channel retrieval. Also reports that EBR
  relevance degrades in practice, which is the relevance-drift risk.
  https://arxiv.org/abs/2106.09297
- **Etsy UEPPR, 2023** (Jha et al., arXiv 2306.04833). The most useful
  paper for us:
  - Motivation: "popular queries typically lack context and have a broad
    intent where additional context from users historical interaction can
    be helpful".
  - Query-tower inputs: recent searches, shop clicks, clicked-item terms,
    and all-time purchase tags, combined with a 1-layer transformer.
  - Results: +5.58% search purchase rate and +2.63% site-wide conversion,
    across A/B tests. Gains were largest for signed-in and habitual buyers.
  - Serving: p99 inference 18 ms, and Faiss with 4-bit PQ loses under 4%
    recall. Two cache-key strategies: include the user/session ID (short
    TTL), or hash the query context into the key (longer TTL).
  https://arxiv.org/abs/2306.04833
- **Unnamed large retailer, 2025** (arXiv 2511.00694). A semantic
  retrieval model with user-level personalization from past purchase
  history and behavior. Reports A/B uplifts in conversion, add-to-cart and
  AOV.
  https://arxiv.org/abs/2511.00694
- **Amazon (Music), 2023 blog and RecSys 2026 paper.** Customer and session
  embeddings are used as the query context in retrieval, and those
  retrieval embeddings are reused as ranking features. This is streaming,
  not retail product search.
  https://www.amazon.science/blog/from-structured-search-to-learning-to-rank-and-retrieve

## Personalized at ranking only (production)

- **Walmart EBR, CIKM 2024** (Lin et al., arXiv 2408.04884). The model is
  query and product only. Personalization via user context is described as
  what *other* platforms do. Hybrid EBR plus lexical retrieval on all
  walmart.com traffic, feeding a reranker. The follow-up at SIGIR 2026
  (arXiv 2607.10096) is still query-product only.
  https://arxiv.org/abs/2408.04884
- **Instacart ITEMS, 2022 blog.** Two towers, query and product only. The
  embedding score is a ranking feature, and the ranker "balances ...
  relevance, popularity, and personal preference".
  https://company.instacart.com/tech-innovation/how-its-made/how-instacart-uses-embeddings-to-improve-search-relevance
- **Airbnb EBR, 2026** (arXiv 2601.06873). The abstract does not say
  whether guest features enter retrieval. Not verified either way.

## Frontier: generative retrieval that merges the stages

- **Kuaishou OneSearch, 2025** (arXiv 2509.03236). A single generative
  model replaces the retrieval/pre-rank/rank cascade, whose stages "suffer
  from fragmented computation and optimization objective collisions". Adds
  user behavior sequences (short and long term). Online: +3.22% orders,
  +2.40% buyers, +1.67% item CTR, with opex reported down 75.4%.
  https://arxiv.org/abs/2509.03236
- **Tmall VARG, 2026** (arXiv 2609.14493). Generative retrieval trained in
  three stages, the last being "personalized retrieval" with expanded user
  context. Its candidates go straight to the final ranker. 14-day A/B on
  20% of traffic: +1.45% GMV.
  https://arxiv.org/abs/2609.14493
- **Personalized query expansion, 2025** (arXiv 2510.08935). An LLM
  rewrites or expands the query using user history before retrieval. This
  is a way to personalize retrieval without a personalized ANN tower.
  https://arxiv.org/abs/2510.08935

## Implications for Search Vision

1. Personalize at both stages. The ranker is always personalized.
   Retrieval gets personalized channels next to a non-personalized
   backbone.
2. Gate personalized retrieval on query breadth: signed-in guest, and a
   broad query where the match set is much larger than K. This matches
   Etsy's head-query finding and saves cost on specific queries.
3. Cheapest channels first:
   - a guest-history channel (repurchase/replenishment, category-filtered)
   - soft personal boosts in the lexical query (size, brand, price tier)
   - then a personalized EBR channel (Etsy-style, ~20 ms p99)
4. Put a relevance filter after the personalized channels (the lesson from
   Taobao and Walmart) and feed embedding similarity to the ranker (the
   lesson from Facebook).
5. Caching still works. The backbone is cached per query and store bucket.
   Personalized channels use Etsy's cache-key strategies or run live.
6. Watch generative retrieval (OneSearch, VARG) as a V3 option. Don't build
   it in V1.

## Caveats

- Company-published A/B results are self-reported and not comparable
  across companies (different baselines and metrics).
- The two closest US retail peers we found (Walmart, Instacart) do not
  personalize retrieval, per their own publications. Neither says they
  tried it and it failed, so it is not evidence against it.
