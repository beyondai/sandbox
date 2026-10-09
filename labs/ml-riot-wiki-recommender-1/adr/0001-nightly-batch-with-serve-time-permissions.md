---
status: accepted
---

# Nightly batch ranking, with permissions filtered at serve time

The panel's ranking for page A depends only on A and on slow history
(28-day opened-next counts, links, text), not on the viewer, and the PRD
allows 24-hour freshness. So a nightly batch ranks up to 100 candidates
per page and stores the top 20 in a key-value store. The request path
only reads `recs[A]`, removes pages the viewer can't access or that are
archived, and shows the top 5. Permissions are the one viewer-dependent
input, and the PRD requires them to apply with no delay, so they are
never baked into the batch.

## Considered options

- **Online scoring per request.** Rejected: a 1-row model call measured
  522 ms p50 and 572 ms p99 on the laptop, against a 150 ms p99 target
  for the whole panel; 50 QPS at peak would need about 40 workers
  (`modeling/05-serve.md`). Nothing in V1 needs request-time inputs.
- **Batch with permissions applied in the batch (per viewer group).**
  Rejected: a permission change would take up to a day to apply, and the
  stored rankings would multiply by the number of permission groups.

## Consequences

- A new page gets model recommendations the night after it is created.
  Until then, a KV miss runs the day-one rule on request.
- The batch stores 20, not 5, so the permission filter can drop up to 15
  pages before the panel shows fewer than 5. Alert when more than 5% of
  panels are short (`design/delivery.md`).
- Session context (V2) and personal features (V3, V4) are request-time
  inputs. They need a light online re-ranker on top of `recs[A]`; that is
  a new decision, not a change to this one.
