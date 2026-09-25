---
status: accepted
---

# One Search Core, separate Channel Front Doors and capacity pools

All four Channels (App/Web, LLM Assistant, Search Engine, Agent) share one
Search Core: catalog and inventory pipelines, the index, query understanding,
retrieval, and one base relevance model. Each Channel gets its own Front Door
(API shape, quotas, auth, SLOs, release gate), its own Ranking Policy on top
of the base model, and its own serving capacity pool as a bulkhead. We chose
this over separate per-Channel stacks because cross-Channel inconsistency (a
product findable in the app but not via ChatGPT, or a different price or
stock) erodes trust, and because relevance work and the store-level inventory
freshness pipeline are too expensive to build N times.

## Considered Options

- **Separate stacks per Channel**: rejected. Its real benefits (different
  objectives, blast-radius isolation, team autonomy, per-Channel abuse
  posture and cost tuning) are kept here through Ranking Policies, capacity
  pools, and Front Doors instead.

## Consequences

- A per-Channel model is only split off when offline metrics show the shared
  base clearly failing that Channel.
- Search Engine is a batch consumer (pre-generated pages), not a live-query
  Channel, but still reads from the same Search Core.
