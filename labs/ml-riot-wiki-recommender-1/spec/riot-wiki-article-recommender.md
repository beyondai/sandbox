prd-hash: 84910b6cbe81b1d298fc7edd2b36912fc35b0076
high-level-hash: b8631619d5e709829d96934a9e60d38142f467bc

# Spec: Riot wiki article recommender

Synthesized 2026-10-08 by the first `ml-modeling-*` step (Quick POC), from
`prd/riot-wiki-article-recommender.md`, `design/high-level.md` and `adr/`.

## Problem Statement

Engineers on the Riot internal wiki (about 40k pages, about 100 new pages a
week) can't find the page they need. Search helps only when the reader
knows what to ask. When a reader is on page A, the wiki must show a panel of
the 5 other pages that are most useful to read next. The goals are less
time spent looking for docs and faster onboarding for new hires.

## Solution

- **Model this folder builds.** One page-to-page graded reranker (V1). The
  candidate generators and the V0 baseline are rules, not models.
- **Two stages.** Rule-based candidate generators (up to 100 per page A),
  then a pointwise learning-to-rank model.
- **Target.** `log1p(r)`, where r = the number of distinct readers who open
  C right after A in the label window.
- **Label and horizon.**
  - Features: [T - 28 days, T). Label: [T, T + 14 days).
  - Pairs with fewer than 3 readers get label 0.
- **Population and cadence.** Every page that is not archived or
  deprecated. A nightly batch scores up to 100 candidates for each page and
  stores the top 20. No personalization in V1.
- **Unit.** One (source page A, candidate page C) pair.
- **Exclusions.** A = C; archived or deprecated pages; near-duplicates (one
  page for each group, cosine over about 0.9); pages the viewer can't access
  (serve time); bot traffic; repeated reloads count once.
- **Feedback loop.** Log the referrer. Panel clicks join training with slot
  position as a feature. Report non-panel transitions as their own slice.
- **Offline architecture.** Named sources -> candidate generators -> nightly
  scoring to the KV store; weekly training of a GBDT on `log1p(r)` with a
  temporal eval against V0 and a registration gate.

## Implementation Decisions

- **Phasing.** V0 baseline rule (no ML) -> V1 GBDT graded reranker -> V2
  session context + exploration bandit -> V3 group personalization -> V4
  per-user (stretch).
- **Complexity gate for V1.** Per-slice routing: the model ranks a query
  slice only where it beats V0 with a 95% CI above 0; V0 ranks the rest;
  not worse overall than V0 alone. New pages are also judged on candidate
  recall. Guardrail: item-side recall@5 on new pages not below V0.
- **Source tables (Riot, assumed).** `wiki.pages`, `wiki.links`,
  `wiki.permissions`, `wiki.page_views`, `recs.impressions`, `recs.clicks`,
  entity dictionaries, `hr.directory` (V3 only).
- **Proxy data in this sandbox.** No Riot data exists here. Modeling runs
  on Wikipedia Clickstream (enwiki 2026-07, 2026-08, 2026-09). Proxy
  differences: monthly click counts, not distinct readers in 14 days; no
  session ids; no page text; pairs with fewer than 10 clicks a month removed
  upstream.
- **Proxy rule.** Wikipedia is evidence, not the target. Every proxy
  finding is translated into a Riot design input ("For Riot" lines in
  `modeling/0N-*.md`). When the two differ, the Riot design wins.
- **Text, embedding and structure features.** Assumed in V1 (user
  decision 2026-10-09): links, page tree, entities, TF-IDF and embedding
  similarity, borrowed clicks, near-duplicate groups, and an embedding
  candidate source. The proxy POC has no text, links or tree, so these are
  designed (`modeling/02-features.md`) but not measured; getting proxy
  data is deferred (`research/page-content.md`).
- **Label sweep.** Done in `ml-modeling-train`: `log1p(r)` kept. sqrt(r)
  and share-of-A's-readers did not win on both new and long_tail; raw r
  with Poisson loss underfit (untuned); LambdaMART not run (LightGBM needs
  the system `libomp`). Details: `modeling/03-train.md`.
- **V1 model.** `HistGradientBoostingRegressor` on `log1p(r)`. On the
  proxy it beats V0 overall and on long_tail, not on new, and is slightly
  worse on head: ship with the hybrid (V0 on head) and the gate on Riot
  data with the text and structure features.
- **ADR 0001.** Nightly batch ranking (top 20 per page in a KV store);
  permissions filtered at serve time.
- **ADR 0002.** V0 is always computed next to V1; a per-slice flag picks
  which one the API reads (the fallback and the V1 rollout).

## Testing Decisions

- **Primary.** nDCG@5 on a temporal next-page replay.
- **Secondary.** recall@5, `recall_w@5` (weighted by clicks), hit@5,
  catalog coverage.
- **Candidate diagnostic.** recall@100 of the candidate generators.
- **Slices.** Age axis (`new`: created < 14 days before T) and traffic
  axis (`dormant`, `long-tail` up to p50, `torso` p50-p90, `head` top 10%),
  each on the query side (panel on A: nDCG@5, recall@5) and the item side
  (C as a recommendation: recall@5 on true next pages). New-hire readers
  are not available on the proxy.
- **Comparison.** Against the V0 baseline (opened-next counts, with
  popularity backfill) and the floor (popularity). Bootstrap 95% CIs.
- **Split rule.** Set by `ml-modeling-data`: train = features 2026-07,
  labels 2026-08; test = features 2026-08, labels 2026-09. Full reasoning in
  `modeling/01-data.md`.

## Out of Scope

- Changes to wiki search ranking.
- An LLM Q&A or RAG assistant, and page summaries.
- LLM-labeled relation types.
- Sources outside the wiki: Google Drive, Jira, Slack, GitHub.
- Push channels: Slack bot, email digests.
- Content cleanup (duplicate groups go to admins only as an output).
- Languages other than English.
