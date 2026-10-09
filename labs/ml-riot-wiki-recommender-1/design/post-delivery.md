# Post-delivery: Riot wiki article recommender

- Mode: Quick POC (2026-10-09). Items marked **(assumption)** are the most
  likely answer, not confirmed by the user. Team names come from the PRD
  (Team, Team - reuse); nobody checked them against a real Riot org.
- Inputs: `prd/riot-wiki-article-recommender.md`, `design/high-level.md`,
  `design/delivery.md`, `modeling/04-evaluate.md`, `adr/0001`, `adr/0002`.

## Analysis

The tests in `design/delivery.md` give the headline: the V0 launch A/B
(guardrails, useful-click rate) and the V1 interleaving (share of users
whose useful clicks favor V1). This plan finds out **why** the result
happened, and for whom. It is written before the tests start, so the
segments and cuts are not chosen after looking at the results.

### Break the primary metric into its parts

```
useful-click rate = clicks / impressions        (does the panel attract?)
                  x useful clicks / clicks      (dwell over 30 s: was it right?)
panel coverage    = panels with 5 pages / views  (was there a panel at all?)
```

- A drop in clicks per impression points to ranking or layout. A drop in
  useful clicks per click points to wrong pages (bounce-backs). A drop in
  coverage points to candidates or the permission filter.
- Read the three parts for each test arm before reading the headline.

### Segments (pre-registered)

- **Query slice** of the page being read: new, dormant, long_tail, torso,
  head. The V1 routing is per slice, so the result must be per slice.
- **Item slice** of the clicked page: new pages shown and clicked, against
  the V0 holdback (the item-side guardrail).
- **Reader tenure:** new hires (first 90 days) against everyone else. New
  hires are a PRD goal (faster onboarding).
- **Page type:** runbook, post-mortem, design spec, onboarding guide,
  knowledge base (from the template or labels).
- **Entry path:** the reader came to A from search, from a link, from the
  panel, or from outside the wiki (Slack, Jira).
- **Period:** the first week against the second, to find a novelty effect.
  Incident days (from the incident tracker) are reported apart, because
  readers move between pages differently during an incident.

### Causes to check

1. **Position.** Click rate by slot 1-5. If slot 1 takes most clicks in
   both arms, the order matters most; if clicks are flat, the set
   matters most.
2. **Candidate source.** For each clicked page, which rule found it
   (opened-next, links, page tree, entities, embedding, borrowed clicks).
   A source with high bounce-back is a bad source, not a bad ranker.
3. **Duplicates and staleness.** Bounce-backs on near-duplicates or
   stale pages show where the duplicate collapse or the stale filter is
   weak.
4. **Cannibalization.** Panel clicks may replace in-body link clicks
   instead of adding to them. Compare the mix of next-page sources and the
   total page views per session (a PRD guardrail) between arms.
5. **Offline-online agreement.** Compare the offline replay delta per
   slice (`modeling/04-evaluate.md` method, on Riot data) with the online
   interleaving result per slice. If they disagree, the offline metric
   needs work before the next model is chosen with it.
6. **Short panels.** Panels with fewer than 5 pages after the permission
   filter, by space. Restricted spaces may need more stored candidates
   than 20.

### Qualitative review

- Each sprint after launch, sample 50 panels with no useful click.
  Label the failure: off-topic, duplicate, stale, too generic (popular
  page), short panel. The counts set the next iteration's priority.
- The reviewers are the ML team and 2-3 volunteers from DevEx.

### Report

- One page to DevEx (the problem owner) after each test: the headline,
  the 3 parts, the slices, the top 2 causes, and the decision (ramp, hold,
  roll back per slice).

## Explainability

The context sets the need: an internal ranking with cheap errors, so
explainability is a soft factor (`ml-design-principles.md`, Principle 1).
It still matters for debugging and for trust in the panel.

### For readers: a short reason under each page

- One reason per recommended page, from the strongest signal:
  - "Linked from this page" (A links to C);
  - "Readers of this page often open it next" (opened-next, 3 or more
    readers);
  - "Same service: <name>" (shared entity);
  - "In the same section" (page-tree sibling);
  - "Similar topic" (embedding or TF-IDF);
  - "New page" (exploration slot, V2).
- Reasons come from fixed rules over the feature values, not from the
  model internals, so they are stable and cheap.
- **Privacy:** a reason never names a reader or a team, and the
  opened-next reason needs 3 or more readers (PRD rules).

### For the team: debugging

- **Per prediction:** SHAP values from a tree explainer on the GBDT, for
  one (A, C) pair: which features pushed C up or down. If the SHAP version
  in the shared env does not support scikit-learn's
  HistGradientBoosting, use per-feature-group ablation for that pair
  (assumption).
- **Per page:** a debug view for page A: every candidate, the rules that
  found it, its features, its score, the routing (model or V0), and how
  many candidates the permission filter removed (a count only, never the
  names).
- **Global:** the feature-group importance per slice (the method in
  `modeling/feature_importance.py`), once a month and after each retrain.
  A large shift (for example the text features taking over the head
  slice) is a review item.

### For stakeholders

- The monthly report to DevEx shows the top signals per slice in plain
  words ("for new pages, most good recommendations come from shared
  service names") and 3 example panels with their reasons.

## Iteration

The roadmap follows `design/high-level.md`, Phasing. The analysis above
decides the order inside each version.

- **V1.1 - tune V1 on Riot data** (2-4 weeks after the V1 switch):
  - re-run the label sweep and the feature importance on Riot logs, with
    the text and structure features (`modeling/02-features.md`);
  - LambdaMART on 0-4 grades, after `libomp` is installed;
  - re-check the head slice: if the model still loses there, keep V0 for
    head pages (no change to the routing flag);
  - stored candidates per page above 20 if short panels show up in
    restricted spaces.
- **V2 - session context and exploration** (Mar 23 - May 15, from
  `design/delivery.md`):
  - the exploration slot for new pages (Thompson sampling, 2 weeks per
    page);
  - candidates and features from the last 3-5 pages in the session;
  - first priority if the item-side new-page guardrail fails in V1.
- **V2.1 - faster freshness for new pages** (if "days to first useful
  click" shows that 24 hours is too slow): an intraday batch for pages
  created that day, in place of the day-one rule on a KV miss.
- **V3 - group personalization** (about 6 weeks after the privacy
  review): owner-team and role affinity; new-hire paths with the
  onboarding team; group aggregates with 5 or more readers.
- **V4 - stretch, not planned:** per-user profiles; LLM-labeled relation
  types ("runbook for", "post-mortem of"), which the PRD keeps out of
  scope for this version.
- **Triggers from the analysis:**
  - high bounce-back on embedding candidates -> raise the duplicate
    threshold, or demote that source;
  - offline and online disagree per slice -> extend the judged set and
    fix the offline metric before V1.1 ships;
  - novelty effect (week 2 well below week 1) -> rotate pages within the
    top 20 to keep the panel fresh.

## Democratize

Components that other teams can reuse (team names from the PRD, Team and
Team - reuse; assumption):

- **Wiki platform admins (IT):**
  - near-duplicate groups (from the embedding pipeline) as a cleanup
    list;
  - a stale-page list: pages with traffic but no edit in 2 years.
- **Wiki search owners:**
  - `recs[A]` from the KV store, for a "related docs" block in search
    results (a PRD downstream consumer);
  - the page embedding index, as a candidate source for semantic search.
- **Developer Experience:** the Recs API, for the Slack bot that answers
  "related docs for this link" (a PRD downstream consumer).
- **People / onboarding:** the new-hire reading paths from V3, and the
  reading-path aggregates, for onboarding checklists.
- **Other ML teams:**
  - the page text and entity pipeline (lead text, embeddings, entity
    extraction) as a shared feature table;
  - the opened-next counts table (distinct readers, 3-reader rule) as a
    behavior feature;
  - the evaluation harness: temporal replay, per-slice and item-side
    metrics, bootstrap CIs (`modeling/evaluate.py`), and the per-slice
    routing gate (`adr/0002`).
- **How:** each component gets an owner, a short README, and a version.
  The feature tables and the API are read-only to other teams; changes
  go through this team's review.

## Change log

- 2026-10-09: created (Quick POC).
