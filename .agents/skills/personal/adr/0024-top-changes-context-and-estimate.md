# Critique: no top-3 cap, context for the share-out, early estimate is P1

## Context

On 2026-10-09, during a merge of 2 critiques, the user corrected 3 rules.
The session logged them as `proposed` in `SKILL-IMPROVEMENTS.md`:
1. The merge asked which item is "item 3" of the top 3. The user: "this
   merge outcome doesn't limit to Top 3 anyways ... don't cut. Sort."
2. On the merged Context section: "context is mostly applied when create
   the share out, not critique or merge."
3. The merge proposed P3 for "no stated latency, QPS, and cost", because
   a precompute makes latency trivial. The user: requirements and cost
   analysis "always need analysis at the beginning."

In the review, the user accepted 1 and 2, and modified 3: "do a quick
back of envelope analysis of reqs and cost analysis. Full one isn't
possible without full design."

## Decision

1. **Top changes, not top 3.** `ml-critique` and `ml-critique-merge`
   start the summary with every P1 item, sorted with the sort key. With
   no P1, the top 3 P2 items. Each is a single change. Only
   `ml-critique-share-out` selects a fixed number (its top 3 messages).
2. **Most of the context is for the share-out.** The critique, the
   lenses, and the merge use the context only for the required parts and
   the scope. The time limit, the format, the sketches, the audience, and
   the topic order are recorded in the Context section with no conflict
   entry, for `ml-critique-share-out`.
3. **A back-of-envelope estimate at the start is P1.** System catalog C2
   becomes `[C]`: a quick estimate of peak QPS, latency, availability,
   freshness, data size, and the order of magnitude of the cost, with
   each assumption marked. It stays P1 when the result looks trivial. A
   full analysis is not asked for at the start; the deep dive refines it
   (F4a, C5). The P1 examples in `ml-critique` name it. The Definition
   checklist and the template ask for the estimate.

## Consequences

- A critique of a weak write-up can start with more than 3 changes. The
  share-out still cuts to fit the time.
- A design with no early estimate gets a P1, even when a review shows the
  cost is small.
- The `ml-critique` eval specs now test "top changes" (every P1). They
  are not run yet (evals on hold for token cost).
