---
status: accepted
---

# V0 is always computed next to V1, and a per-slice flag picks one

The nightly job writes two rankings for every page: `recs_v1[A]` (the
model) and `recs_v0[A]` (the PRD baseline rule). A config flag per query
slice (new, dormant, long_tail, torso, head) chooses which one the API
reads. This is the fallback (one flag change, no redeploy, no recompute),
and it is also how V1 ships: on the Wikipedia proxy the model wins only on
long_tail and torso pages, ties on new pages and loses slightly on head
pages (`modeling/04-evaluate.md`), so the design gate routes per slice
(`design/high-level.md`).

## Considered options

- **Ship one ranker and roll back by redeploying the previous model.**
  Rejected: a rollback takes a deploy plus a full nightly recompute, and
  it can't keep V1 where it wins while dropping it where it loses.
- **Blend the two scores.** Rejected: the model and the rule score on
  different scales, and a blend is harder to explain and to roll back
  than a per-slice choice.

## Consequences

- Twice the KV storage (about 80 MB for 40k pages) and a second, simpler
  batch job that must keep working even when the model pipeline fails.
- The V0 rule can never be deleted while V1 is live. It is also the
  baseline for the 5% holdback that monitoring compares against.
- Each query slice is known at scoring time (page age and history), so
  routing is a table lookup, not a model.
