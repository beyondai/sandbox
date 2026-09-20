# PRD: Ecommerce Product Search

Scoped via `/ml-system-design-prd`. Covers Definition only (problem, requirements, metrics, team) — high-level design, deep dive, delivery, and post-delivery follow in the corresponding `ml-system-design-*` skills.

## Problem

On-site search conversion underperforms the industry benchmark — no ML-driven ranking or retrieval exists in production today. Driven by the Director of Search to close this gap; search-session users convert at 2-3x the rate of non-search sessions industry-wide when search works well, so this is a large, currently-uncaptured revenue lever.

Goal: reach top-quartile search-session conversion (4-6%, vs. ~4.63% industry average / top-performer range).

## Requirements

### Scope

**V1 must-have:**
- Hybrid retrieval: lexical (Solr/Elasticsearch inverted index) + vector/semantic (embedding-based) candidate generation
- ML-driven ranking layer over combined retrieval candidates
- Faceted filtering (category, price, brand)
- Typo tolerance / query understanding
- Graceful-degradation fallback to lexical-only ranking when the ML/vector layer is unavailable

**Out of scope V1:**
- Per-user personalization
- Visual search / voice search
- Multi-language support

### Non-functional

- Scale: 50M SKUs, 10K QPS peak
- Latency: p99 < 600ms
- Availability: 99.99%, with lexical-only fallback as the degradation path

## Metrics

**Offline:** nDCG@10, Precision/Recall@k, MRR on a held-out query set.

**Online:** search-session conversion rate (target 4-6%).

**Guardrails:** zero-result rate < 2%, p99 latency < 600ms, 99.99% availability.

## Team

- **Stakeholder:** Director of Search
- **Collaborating teams:** Catalog/Data Platform (product data feed), Data/ML Platform (data warehouse + model-serving infra, reused)
- **Dependency:** catalog data assumed available via existing product DB
- **Reuse:** general data warehouse + model-serving platform only — indexing pipeline, feature pipeline, ranking model, and the full lexical+vector retrieval stack are all net-new builds
- **Downstream consumers:** none identified — TBD

## Assumptions carried into this doc

- Practice/real-project treated with stated assumptions rather than a real company name
- Greenfield build — no existing search system of any kind in production
- Single-retailer catalog (not marketplace)
- General merchandise vertical (unstated — anchored to broadest default)
- Catalog data exists in a transactional/product DB; this project does not build catalog data management from scratch
