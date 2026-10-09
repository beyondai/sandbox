# High-level design: Riot wiki article recommender

- Mode: Quick POC (2026-10-08). Items marked **(assumption)** are the most
  likely answer, not confirmed by the user.
- Inputs:
  - `prd/riot-wiki-article-recommender.md` (Definition, including Baseline);
  - `research/cold-start.md`;
  - `research/personalization.md`;
  - `monkey-mode/report.md` (Wikipedia proxy results).

## ML framing

**One sentence.** For each source page A, rank candidate wiki pages C by the
expected number of distinct readers who will open C right after A, and show
the top 5 that pass the permission and duplicate filters. This is a
two-stage retrieve-then-rank problem: rule-based candidate generators, then
a pointwise learning-to-rank model with graded labels.

This folder builds: **the page-to-page graded reranker** (V1 below).
- The candidate generators are rules, not models.
- The V0 baseline is a rule.
- Personalization models (V3, V4) get their own project folders.

Backing for the reranker:

- **Prediction target.** `log1p(r)`, where r = the number of distinct readers
  who open C right after A (same session) in the label window.
- **Label definition and horizon** (assumption).
  - Choose a cutoff time T.
  - Features use only data from [T - 28 days, T).
  - Label: `log1p(r)` over [T, T + 14 days).
  - A pair with fewer than 3 distinct readers gets label 0. Below 3 readers
    the signal is mostly noise, and the PRD's privacy rule uses the same
    minimum.
  - The label is graded, not "clicked or not". In the monkey-mode run, a
    binary label lost 8% nDCG@5; the graded label fixed it.
- **Scoring population and cadence.**
  - Every page that is not archived or deprecated: about 40k pages (PRD
    estimate).
  - A nightly batch scores up to 100 candidates for each page. It stores
    the top 20, so 5 remain after the permission filter at serve time.
  - V1 recommendations are the same for every viewer (no personalization).
- **Unit of prediction.** One (source page A, candidate page C) pair.
- **Exclusions and contamination.**
  - A = C, and archived or deprecated pages, as source or candidate.
  - Near-duplicates: one page for each near-duplicate group (cosine over
    about 0.9). The newest or canonical page represents the group.
  - Pages the viewer can't access. Removed at serve time, never only at
    training time.
  - Traffic that is not a human reader (assumption): crawlers, link
    checkers, monitoring tools, dashboard auto-refresh. Repeated reloads by
    one reader count once.
  - **Feedback loop.** After launch, many A -> C transitions come from the
    panel itself, so the model would learn from its own output. Each page
    view logs its referrer (panel, link, search). Panel clicks join
    training with their slot position as a feature, set to a fixed value at
    scoring time. Report the non-panel transitions as a separate eval
    slice.
- **Primary metric.** The PRD's: nDCG@5 on a temporal next-page replay
  (PRD, Metrics - offline). This design does not change it.

## Architecture

### Online inference (request path)

```
reader opens page A
   |
   v
wiki UI ---(async, after page render)---> Recs API            p99 < 150 ms
                                             |
                       +---------------------+---------------------+
                       v                     v                     v
               KV store: recs[A]     permissions check     page status check
               (top 20, scores,      (wiki permissions     (archived /
                model version)        API, cached per       deprecated)
                       |              viewer + space)              |
                       +---------------------+---------------------+
                                             v
                               filter -> exploration slot (V2+)
                                             v
                                   top 5 -> wiki UI panel
                                             |
                                             v
                     impression log: request_id, viewer hash, page A,
                     5 page ids, positions, model version, timestamp
                     click log: request_id, clicked page, dwell time

fallback:  KV miss  -> day-one baseline rule for A (computed on request)
           API down -> panel hidden, page works as normal
```

### Offline training and batch scoring

Named sources (assumption: a Confluence-like wiki):

- **`wiki.pages`**: page id, title, body, space, parent (ancestors),
  author, owner team, labels, template, status, created and modified times.
  From the wiki REST export.
- **`wiki.links`**: (from page, to page), parsed from page bodies.
- **`wiki.permissions`**: space and page restrictions.
- **`wiki.page_views`**: hashed user id, session id, page id, timestamp,
  referrer type (panel / link / search / external). From wiki access logs.
- **`recs.impressions`** and **`recs.clicks`**: our own panel logs (online
  diagram).
- **Entity dictionaries**: the service catalog, GitHub repo list, Jira
  project keys, Slack channel list.
- **`hr.directory`**: team and role. V3 only, after privacy review.

```
wiki.pages ------+--> parse: text, entities, embeddings, near-dup groups --+
wiki.links ------+--> link graph (out-links, back-links)                    |
(page tree) -----+--> page tree (parent, siblings)                          |
entity dicts ----+--> entity index (page <-> service/repo/Jira/Slack)       |
wiki.page_views -+--> opened-next counts (distinct readers, >= 3, 28 days) -+
recs.impressions/clicks -> panel-referrer flags, slot positions ------------+
                                                                            v
                   candidate generators (rules, union, cap 100 per page)
                   links | page tree | entities | topic | borrowed clicks |
                   opened-next
                                            |
                  nightly                   |                  weekly
          +---------------------------------+------------------------+
          v                                                          v
 features -> score with current model                 labeled table (cutoff T)
 (V0: baseline rule) -> top 20 per page               -> train GBDT on log1p(r)
          -> KV store                                 -> eval: temporal replay,
                                                         nDCG@5 vs V0 baseline,
                                                         slices + bootstrap CI
                                                      -> register model only if
                                                         it passes the gate
```

- The nightly job uses the latest registered model. If the training gate
  fails, the previous model stays in use.
- Permissions are filtered at serve time, so a permission change takes
  effect immediately (PRD freshness requirement).

## Phasing

PRD personalization phases V1-V4 map onto this plan. PRD "V1 non-p13n"
becomes V0 (rule) plus V1 (model) here.

```
V0 baseline rule -> V1 reranker -> V2 session + exploration -> V3 group -> V4 per-user
   no ML            GBDT             bandit slot                team/role     stretch
```

### V0 - baseline (no ML)

- **Ships.**
  - The panel.
  - Day-one rule (PRD Baseline): out-links + back-links + page-tree
    siblings, ranked by 30-day page views.
  - Near-duplicate collapse, permission and status filters.
  - Impression, click and referrer logging.
  - After about 4 weeks of logs: opened-next popularity, with empty slots
    filled by the day-one rule.
- **Model class.** Baseline: a rule, no ML.
- **Timeline** (assumption): 5-6 weeks. Most of it is data access, the UI
  slot and logging, not modeling.
- **Headcount** (assumption): 1 MLE, 0.5 backend engineer, plus wiki UI
  support.
- **Why this phase.** It sets the bar, collects the logs that every later
  phase needs, and stays as the production fallback.

### V1 - first real model: graded reranker

- **Ships.**
  - More candidate sources from `research/cold-start.md`: shared entities,
    topic similarity with duplicates removed, and borrowed clicks (where
    readers of the 10 most similar warm pages went next).
  - A GBDT regression on `log1p(r)` over all candidate features: opened-next
    counts, link and tree relations, entity overlap, cosine similarity, page
    age, views, owner team.
- **Model class.** First real model.
- **Timeline** (assumption): 6-8 weeks after V0 has 4 weeks of logs.
- **Headcount** (assumption): 1-2 MLE.
- **Expected gain over V0.**
  - Mostly on cold, new and long-tail pages.
  - On the Wikipedia proxy, the graded reranker scored cold-page nDCG@5 of
    0.257 against 0.0014. On warm pages it gained only +0.5% over
    opened-next counts.
- **Complexity gate** (`../../.agents/skills/personal/ml-design-principles.md`,
  Principle 1):
  - It must beat V0 on the cold and long-tail slices, with a CI that
    excludes 0.
  - It must not be worse overall.
  - If it fails on warm pages, keep the V0 rule for warm pages and use the
    model only for cold and long-tail pages (the monkey-mode hybrid
    pattern).

### V2 - session context and exploration for new pages

- **Ships.**
  - An exploration slot: 1 of 5 slots on related warm pages goes to a new
    page for up to 2 weeks, chosen by Thompson sampling.
  - Session context: candidates and features from the last 3-5 pages in the
    session.
- **Model class.** The V1 reranker, a bandit for the slot, and new session
  features.
- **Timeline** (assumption): 4-6 weeks.
- **Headcount** (assumption): 1 MLE, 0.5 backend engineer.
- **Expected gain over V0.**
  - New pages get their first useful clicks sooner. This needs a new metric:
    days to first useful click for new pages.
  - Readers in a multi-page task get more useful clicks.
- **Needs.** A session id in `wiki.page_views`.

### V3 - group personalization

- **Ships.**
  - An owner-team boost: pages owned by the viewer's team or adjacent teams.
  - Team and role affinity.
  - New-hire paths for each role.
- **Model class.** V1 reranker plus viewer-group features.
- **Timeline** (assumption): about 6 weeks after the privacy review.
- **Headcount** (assumption): 1 MLE, plus the onboarding team for the paths.
- **Expected gain over V0.** Mostly for new hires and for pages whose
  meaning depends on the team (for example, a generic "Deploy" page).
- **Needs.**
  - `hr.directory`.
  - Privacy and legal sign-off.
  - Group aggregates with at least 5 readers.

### V4 - stretch: per-user models

- **Ships.** A user profile vector or a sequence model. LLM-labeled relation
  types ("runbook for", "post-mortem of").
- **Model class.** Stretch.
- **Timeline and headcount.** Not planned. Start only if V3 logs show enough
  per-user signal to pass the complexity gate.

## Open items for the next step

- **Fork.** The paper route is `ml-system-design-deep-dive`. The hands-on
  route is `ml-modeling-*`. Riot data is not available in this sandbox, so a
  hands-on route would run on the Wikipedia Clickstream proxy with a
  temporal split (2026-08 features, 2026-09 labels).
- **ADR candidate.** Nightly batch precompute plus serve-time permission
  filtering, instead of online scoring. It is hard to reverse, and it fixes
  the 24-hour freshness for new pages.
- **Label sweep (decided by the user, 2026-10-08).** Keep `log1p(r)` as the
  V1 default. It matches the nDCG@5 gain and won in monkey-mode. In the
  modeling step, run a short sweep of label options. Change the model and
  the loss to match each label:

  ```
  label                         model and loss
  -----                         --------------
  log1p(r)        (default)     GBDT regression, squared error
  raw r                         GBDT regression, Poisson loss
  sqrt(r)                       GBDT regression, squared error
  share r / readers leaving A   GBDT regression, squared error
                                (or Poisson on r, offset by log of
                                readers leaving A)
  grade buckets 0-4             LambdaMART ranking loss, grouped by A
                                (needs LightGBM: uv add at sandbox root)
  ```

  - Compare on nDCG@5 and `recall_w@5` (weighted by raw clicks), overall
    and for each traffic bucket.
  - Keep the nDCG gain fixed at `log1p` for every option, so the scores
    can be compared.
  - Pick the option that wins on cold and long-tail pages without losing
    overall. If no option beats `log1p(r)` with a CI that excludes 0, keep
    the default.
  - A label change needs new training runs. The saved-outputs eval-only
    re-run does not cover it.

## Change log

- 2026-10-08: created (Quick POC).
- 2026-10-08: added the label sweep to Open items (user decision: log1p
  default, sweep in modeling, model and loss follow the label).
