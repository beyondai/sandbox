# Design Deep Dive: Ecommerce Product Search

Backfilled from the earlier High-level Design conversation (see [`../adr/0001-ecommerce-search-hybrid-architecture.md`](../adr/0001-ecommerce-search-hybrid-architecture.md)) — this file didn't exist yet when that ADR was written; written now via `ml-system-design-deep-dive`'s new file-writing behavior.

## Data

**Real-time inference sources:** query text, product catalog index (lexical + vector), live stock/availability status. No user identity/history — personalization is out of scope for V1.

**Batch training sources:** search logs (query, impressions, clicks, purchases), catalog DB (title, description, category, price, stock, images), computed product embeddings.

**New data engineering:** ETL joining impression/click/purchase logs into a unified training set; catalog indexing pipeline (lexical index + embedding generation + ANN index build); feature pipeline computing query-product features consistently at training and serving time (training/serving skew risk, called out explicitly).

**Real gap:** no search system exists yet, so no query-level click/purchase logs exist either. V1's ranking model and retrieval embedding model both need labeled (query, product, clicked/purchased) data, which can only come from V0 (lexical-only) running in production first — a hard scheduling dependency the phasing doesn't otherwise surface.

## Features

**Query:** raw text, normalized/tokenized text, spell-corrected text, query length.

**Product:** title/description text embedding, category, price, brand, stock status, popularity/sales-rank (derivable from pre-existing site purchase logs), average rating.

**Query-product interaction:** BM25/lexical match score, embedding cosine similarity, exact-term-match signals, aggregate historical CTR for this product on similar queries (population-level, not per-user).

**Contextual:** device type, time of day, day of week. No user-identity features.

**Nontrivial engineering:** generating and maintaining embeddings for the full 50M-SKU catalog as it changes; an ANN index that serves within the 600ms p99 latency budget — the ANN algorithm choice needs its own latency budget, not just an accuracy target.

## Models

**Retrieval (embedding) model** — candidates: (a) pretrained sentence-transformer fine-tuned on click pairs, or (b) a two-tower model trained from scratch. Chose (a) for V1: ships faster, needs far less data than (b), which matters given the cold-start data gap above.

**Ranking model** — candidates: GBDT with a pairwise/listwise ranking objective (LightGBM/XGBoost) vs. a deep two-tower/cross-network. Chose GBDT for V1: strong on tabular + similarity-score features, fast to train, interpretable, fits a 5-person team's infra budget; doesn't natively consume raw embeddings (needs them pre-reduced to a similarity score first). Deep ranking is a natural V2 upgrade once more labeled data exists.

## Training

**Ranking model:** listwise ranking loss (LambdaMART/NDCG-based) rather than plain binary cross-entropy — matches the offline eval metric (nDCG@10) instead of optimizing a proxy that doesn't.

**Retrieval model:** contrastive loss over (query, clicked-product) positive pairs with sampled negatives (in-batch or random-from-catalog).

**Labels:** purchase = strong positive, click = weak positive, impression-without-click = negative — graded, not flat binary.

**Sampling:** ranking model needs negative downsampling (most impressions aren't clicked); retrieval model needs explicit negative sampling since only positives are logged naturally (random negatives to start, hard negatives — high BM25 score but not clicked — once there's enough volume to mine them).
