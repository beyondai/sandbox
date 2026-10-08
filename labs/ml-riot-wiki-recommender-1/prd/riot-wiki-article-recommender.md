# PRD: Riot wiki article recommender

- Status: confirmed by the user, 2026-10-08 (Quick POC grilling, 2 rounds).
- Project folder: `labs/ml-riot-wiki-recommender-1/`.
- Inputs:
  - `notes/riot-wiki-article-recommender.md` (the brief);
  - `research/personalization.md` (personalization notes);
  - `research/proxy-datasets.md` (proxy data);
  - `monkey-mode/report.md` (proxy baseline results).

Task, in the brief's words: "Build a system that, given the article a user
is currently viewing, recommends 5 other articles they might find useful."

## Problem

- **Core problem.** The internal wiki has tens of thousands of pages:
  post-mortems, design specs, onboarding guides, runbooks and knowledge base
  articles. Engineers can't find the page they need. New hires spend a lot of
  time searching for docs during onboarding.
- **Gap.** Search only helps when the reader knows what to ask. It does not
  show "what to read next" from the page the reader is on.
- **Why now.** The wiki grows every week. Each new page makes the right page
  harder to find.
- **Growth estimate (assumption, to verify).**
  - About 40k pages today.
  - About 100 new pages a week (about 5k a year, about +12% a year).
  - About 1k edited pages a week.
  - Basis: tens of thousands of pages built over about 8-10 years.
  - Check: count page creation dates through the wiki API before the design
    is final (about one hour of work).
  - Effect: about 100 pages a week start with no clicks. Cold start is a
    permanent load, not only a launch problem. A nightly batch is fast
    enough for this rate.
- **Goal links.**
  - Engineer productivity: less time spent looking for docs.
  - Faster onboarding: shorter time to first contribution for new hires.

## Requirements - scope

### Must-have (V1)

- **Panel.** A "Related articles" panel on each wiki page. It shows the top 5
  pages for the current page.
- **Day-one method: logical connection, not duplicates.** Plain text
  similarity ranks near-duplicates highest (copied runbooks, post-mortems
  from one template), so it is not the ranker. V1 uses structure signals that
  need no click logs:
  1. **Link graph:** out-links and back-links. In the monkey-mode proxy run,
     reverse edges gave almost all of the cold-page lift.
  2. **Page tree:** parent, children and siblings in the same space.
  3. **Shared entities:** pages that name the same service, repo, Jira
     project or owner team. Example: a post-mortem connects to the runbook
     for the same service.
  4. **Topic similarity:** one feature among the others, not the ranker.
     Near-duplicates (cosine over about 0.9) form one group. Only the newest
     or canonical page of a group can be shown. MMR keeps the top 5 diverse.

  ```
  candidates (no click logs needed)
    links: out-links, back-links      --+
    page tree: parent, children,        |
      siblings                          +--> dedupe --> rank --> top 5
    shared entities: service, repo,     |
      Jira project, owner team          |
    topic similarity (embeddings)     --+
  ```

- **Clicks when they exist.** Add co-view click features in a graded
  reranker (trained on click volume, not "clicked or not"; see the
  monkey-mode result).
- **Permissions.** Filter every recommendation by the viewer's access
  permissions.
- **No archived pages.** Do not show archived or deprecated pages.
- **Logging.** Log impressions and clicks for evaluation and retraining.

### Personalization path (in the design, phased)

The design covers both non-personalized and personalized recommendations.
Each phase uses only the data that exists by then.

```
V1  non-p13n    current page only (signals above + clicks when they exist)
V2  context     + session context (last 3-5 pages)      needs session id
V3  group       + team/role affinity, new-hire paths    needs HRIS join
V4  per-user    + user profile vector                   needs per-user logs
```

- **Personalization with no reading logs.**
  - Join the viewer's team (from the directory) to the page owner team.
  - Boost pages that the viewer's team or adjacent teams own.
  - New hires get onboarding paths per role. Onboarding owners curate them.
- **Rules for all phases** (from `research/personalization.md`):
  - A group aggregate needs at least 5 readers.
  - Never show who read what.
  - Users can opt out.
  - A fixed share of results is not personalized, so readers still find
    pages outside their team.

### Out of scope (this version)

- Changes to wiki search ranking.
- An LLM Q&A or RAG assistant, and page summaries.
- LLM-labeled relation types ("runbook for", "post-mortem of"). This is a
  later step, not V1.
- Sources outside the wiki: Google Drive, Jira, Slack, GitHub.
- Push channels: Slack bot, email digests.
- Content cleanup: duplicate removal, stale-page flagging. The duplicate
  groups are only given to admins as an output (see Team - reuse).
- Languages other than English.

## Requirements - non-functional

Scaled to an internal tool. These numbers are assumptions to check.

- **Load.**
  - A few thousand employees at about 30 page views a day each gives about
    4 views/s on average.
  - Plan for 50 QPS at peak.
- **Latency.**
  - p99 under 150 ms for the panel.
  - A nightly batch precomputes recommendations for each page. Serving is a
    key-value lookup.
  - The panel loads asynchronously and never blocks the page.
- **Availability.** 99.5%. The system is not critical. If it fails, the
  panel hides and the page still works.
- **Freshness.**
  - A new or edited page gets recommendations within 24 hours.
  - Permission changes take effect at serve time, with no delay.

## Metrics - offline

- **Primary.** nDCG@10 on next-page replay from Riot wiki logs.
- **Split.** A temporal split: history weeks, then future weeks. Do not use
  random thinning. The monkey-mode run showed that thinning makes the click
  baseline look near-perfect (nDCG@10 0.97).
- **Secondary.** recall@10 and catalog coverage.
- **Slices.**
  - cold and new pages;
  - **long-tail** pages (low traffic);
  - new-hire readers.
- **Before logs exist.** A judged set of about 200 seed pages. Domain experts
  choose the top 5 relevant pages for each. Score with nDCG@5.

## Metrics - online

The panel's job is to show 5 useful pages for the current page. The online
metrics measure that job only. Search metrics are not used.

- **Primary.** Useful-click rate = panel clicks with dwell time over 30 s,
  divided by panel impressions.
- **Secondary.**
  - Panel-driven page views per session.
  - Bounce-back rate: a click followed by a return in under 10 s. This means
    a bad recommendation.
  - Coverage: the share of pages that show 5 recommendations.
- **Guardrails.**
  - Page load time.
  - Zero permission leaks.
  - Share of recommendations that point to stale pages.
  - Share of duplicates in the top 5.
  - Total wiki page views per session must not drop.
- **Test design.** Randomize by user. A few thousand users give low
  statistical power, so add team-draft interleaving. Interleaving detects
  ranking differences with far fewer users.

## Team

- **Owner.** The ML engineering team.
- **Stakeholders.**
  - Developer Experience / Engineering Productivity (the problem owner).
  - People / onboarding (new-hire paths, the onboarding survey).
  - Wiki platform admins (IT).
- **Blocking dependencies.**
  - **Wiki platform:** access to page content and the permissions API.
  - **Page-view logs:** they must include a session id.
  - **Privacy and legal review:** must approve logging of reading behavior
    before V2.
  - **Wiki UI:** a slot for the panel, from the wiki platform team.
- **What we block.** Nothing at V1. At V3 the onboarding team depends on us
  for new-hire paths.

## Team - reuse

These are assumptions. This is a sandbox, so nobody checked them against a
real Riot stack.

- **Reuse, do not rebuild.**
  - The wiki's search index, for entity and keyword lookups.
  - An internal embedding or LLM service, if one exists.
  - The batch scheduler and key-value store, for precomputed
    recommendations.
  - The A/B test framework.
- **Downstream consumers.**
  - A related-docs block in search results.
  - A Slack bot that answers "related docs for this link".
  - Onboarding checklists.
  - Duplicate groups, given to wiki admins as a cleanup list.

## Change log

- 2026-10-08: created from two Quick POC grilling rounds (Q1-Q12).
- 2026-10-08: moved the two generated notes into `research/`. Notes/ keeps
  only content the user wrote or pasted.
