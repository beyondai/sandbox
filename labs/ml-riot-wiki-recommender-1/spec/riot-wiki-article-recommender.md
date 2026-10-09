prd-hash: 53935f1fb2ee5e70b5ae45c9f7e31bc957f5cc02
high-level-hash: 1dba2a6f6da6ad6713a86da4e4c7d46362e54bdd

# Spec: Riot wiki article recommender

Synthesized 2026-10-08 by the first `ml-modeling-*` step (Quick POC), from
`prd/riot-wiki-article-recommender.md` and `design/high-level.md`. There is
no `adr/` yet.

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
- **Complexity gate for V1.** It must beat V0 on the cold and long-tail
  slices with a CI that excludes 0, and must not lose overall. Otherwise:
  V0 for warm pages, model for cold and long-tail pages (hybrid).
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
- **Label sweep.** `log1p(r)` is the V1 default. The modeling step sweeps
  raw r (Poisson loss), sqrt(r), share of A's readers, and 0-4 grades
  (LambdaMART). The model and the loss follow each label.
- **ADRs.** None yet. Candidate: nightly batch precompute plus serve-time
  permission filtering.

## Testing Decisions

- **Primary.** nDCG@5 on a temporal next-page replay.
- **Secondary.** recall@5, `recall_w@5` (weighted by clicks), hit@5,
  catalog coverage.
- **Candidate diagnostic.** recall@100 of the candidate generators.
- **Slices.** cold and new pages, long-tail pages, new-hire readers (not
  available on the proxy).
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
