---
status: accepted
---

# Tiered LLMs: self-hosted small models hot, internal OpenAI heavy

High-volume, latency-critical LLM work (query understanding, rewriting,
attribute extraction, Query Router) runs on self-hosted small models.
Expensive, low-volume steps (Guided Shopping planning, longer Conversational
Search answers) use the OpenAI models Target already hosts internally, behind
one LLM gateway. A per-query frontier API call at 10k+ QPS would break both
the token budget and the 150 ms Keyword Search p99, while frontier quality
only pays off on the small share of traffic that needs it.

## Considered Options

- **Third-party APIs only**: rejected on cost and latency at hot-path volume.
- **Self-hosted only**: rejected; gives up frontier quality exactly where
  Guided Shopping needs it, and ignores the existing internal OpenAI hosting.
