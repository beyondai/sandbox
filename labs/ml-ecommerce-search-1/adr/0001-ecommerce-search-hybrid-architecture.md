# Ecommerce search: hybrid retrieval + ML ranking architecture

Requirements in [`docs/prd/ecommerce-search.md`](../prd/ecommerce-search.md). Context: no search system exists today; the goal is top-quartile search-session conversion (4-6%). We're building lexical retrieval (Solr/Elasticsearch), vector/semantic retrieval, and an ML ranking layer over the combined candidates, framed as: predict a relevance/purchase-intent score for each `(query, product)` pair over a hybrid candidate set, and rank by it. Lexical retrieval doubles as the fallback tier when the ML/vector path is unavailable, and ships first (V0) both to de-risk the build and to establish a real pre-ML baseline, since none exists to measure the 4-6% target against.

## Architecture

**Online inference:**

```
User query
    │
    ▼
Query Understanding (spell correction, typo tolerance, parsing)
    │
    ├──────────────┬──────────────────────┐
    ▼              ▼                      │
Lexical retrieval  Vector retrieval       │
(Solr/ES BM25)     (ANN over embeddings)  │
    │              │                      │
    └──────┬───────┘                      │
           ▼                              │
   Candidate merge + dedup                │
           ▼                              │
   Feature enrichment                     │
   (product + query-product features)     │
           ▼                              │
   ML ranking model (scores candidates)   │
           ▼                              │
   Business rules (in-stock, facets)      │
           ▼                              │
   Results ──────────────────────────────►│
                                           │
   [ML/vector path unhealthy or times out]│
           │                              │
           └──► Lexical-only fallback ────┘
                (BM25 rank, no ML)
```

**Offline training:**

```
Product DB (catalog)                 Search logs
    │                                 (impressions, clicks, purchases)
    ▼                                      │
Catalog indexing job                       ▼
    │                              Label generation
    ├──► Lexical index (Solr/ES)   (click/purchase = positive)
    │                                      │
    └──► Embedding generation ─────┐       │
         (vector index)            │       │
                                    ▼       ▼
                            Feature pipeline
                            (product + query + interaction features)
                                    │
                                    ▼
                          Training dataset construction
                                    │
                                    ▼
                            Model training
                                    │
                                    ▼
                    Offline eval (nDCG, Precision/Recall, MRR)
                                    │
                                    ▼
                    Model registry → serving infra (reused platform)
```

## Phasing

- **V0 (crawl), ~6-8 weeks, all 5 engineers:** lexical retrieval, catalog indexing, facets, typo tolerance, BM25 + business-rule ranking. This is the fallback tier, built first. Ships the pre-ML baseline.
- **V1 (walk), remainder of the 6-12 month window, same 5 split ~2 retrieval / ~2 ranking / 1 eval:** adds vector retrieval + ML ranking on top of V0.
- **V2 (run), next planning cycle, unsized:** personalization, visual/voice search, multi-language.

## Considered Options

Recommended (b) — full hybrid retrieval + ML ranking for V1 — was accepted over (a) — ship V1 as an ML re-ranker on top of lexical-only retrieval, deferring vector retrieval to V2. (a) was the lower-risk option: it isolates ranking-model risk from retrieval-infra risk and ships faster. (b) was chosen anyway because vector retrieval was treated as required for V1, not deferrable.

## Consequences

- V1 carries combined retrieval-infra and ranking-model risk in one release, rather than isolating them across two.
- V0 exists as a real phase (not skipped straight to V1) specifically because it's needed both as the fallback tier and as the only way to get a pre-ML conversion baseline.
