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
- **Slices: age and traffic, query side and item side** (PRD, Slices).
  Cold-start and long-tail are different problems:

  ```
  axis      slice       meaning                        main fix
  age       new         created < 14 days before T;    structure candidates
                        no evidence yet                (query side),
                                                       exploration (item side)
  traffic   dormant     established, 0 views in 28 d;  show only on strong
                        evidence of no demand          structure signals
            long-tail   views up to p50                smoothing, two-hop,
                                                       borrowed clicks
            torso/head  p50-p90 / top 10%              opened-next counts
  ```

  - Query side: the panel on page A. Item side: page C as a
    recommendation, scored by recall@5 on true next pages in each slice.
  - Features use page age and counts per day since creation, so a 3-day-old
    page with 20 readers is hot, not long-tail.

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
  - More candidate sources from `research/cold-start.md`: the page's own
    out-links and back-links (`wiki.links`), page-tree siblings, shared
    entities, embedding nearest pages with duplicates removed, and
    borrowed clicks (where readers of the 10 most similar warm pages went
    next).
  - Text and embedding pipeline (assumed in V1, user decision 2026-10-09):
    - text: title + headings + lead (about 300 words) per page;
    - TF-IDF and a small sentence-embedding model (internal service if one
      exists, else about 30M parameters, 384 dimensions, CPU);
    - an ANN index for nearest pages, and near-duplicate groups (cosine
      over about 0.9);
    - entity extraction against the entity dictionaries.
  - A GBDT regression on `log1p(r)` over all candidate features (full list
    in `modeling/02-features.md`):
    - clicks: opened-next, reverse, two-hop;
    - structure: is linked from A, back-link, same parent or space;
    - text: `cos_tfidf`, `cos_emb`, `title_overlap`, `shared_entities`,
      `borrowed_clicks`, template pair;
    - page: age, counts per day since creation, views, last edit, owner
      team;
    - candidate-rule flags.
  - Cost: about 40k pages; a full embedding backfill is minutes on CPU;
    the nightly update covers about 100 new and 1k edited pages a week.
- **Model class.** First real model.
- **Timeline** (assumption): 6-8 weeks after V0 has 4 weeks of logs.
- **Headcount** (assumption): 1-2 MLE.
- **Expected gain over V0.**
  - Mostly on new and long-tail pages, query side and item side.
  - On the Wikipedia proxy, the graded reranker scored cold-page nDCG@5 of
    0.257 against 0.0014. On warm pages it gained only +0.5% over
    opened-next counts.
  - The proxy has no text, links or tree, so its numbers for new and
    dormant pages are lower bounds. The text and structure features are
    designed in, but not measured (`research/page-content.md` has the plan
    to measure them).
- **Complexity gate** (`../../.agents/skills/personal/ml-design-principles.md`,
  Principle 1):
  - **Per-slice routing.** Decide for each query slice (new, dormant,
    long_tail, torso, head) on its own. The model ranks a slice only if it
    beats V0 there with a 95% CI above 0. V0 ranks every other slice. The
    slice is known at scoring time (page age and history), so routing is a
    lookup, not a model.
  - It must not be worse overall than V0 alone.
  - **New pages are judged on two numbers:** candidate recall (does the
    right page reach the candidates?) and nDCG@5 against the full truth.
    nDCG over the candidates alone hides a candidate miss.
  - **Item-side guardrail.** The shipped ranker must not show new pages
    less often than V0 (item-side recall@5 on new pages, CI not below 0).
    On the proxy, the model alone fails it (-1.4 points); the hybrid
    loses 0.3 points (`modeling/04-evaluate.md`).
  - V1 counts as a success if it wins on long_tail, and on new pages once
    the structure and text candidate sources are live. Content and
    structure are necessary for new pages; the size of their gain is not
    measured yet (`research/page-content.md`, "Conclusions").
  - Proxy status (`modeling/03-train.md`): the model wins on long_tail and
    torso, ties on new and dormant, and loses slightly on head. Routing:
    model for long_tail and torso, V0 for the rest.

### V2 - session context and exploration for new pages

- **Ships.**
  - An exploration slot: 1 of 5 slots on related warm pages goes to a new
    page for up to 2 weeks, chosen by Thompson sampling.
  - New pages only (age < 14 days). Dormant and long-tail pages don't get
    the slot: their low demand is already known, so exploring them costs
    traffic and teaches little.
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
  - Pick the option that wins on new and long-tail pages without losing
    overall. If no option beats `log1p(r)` with a CI that excludes 0, keep
    the default.
  - A label change needs new training runs. The saved-outputs eval-only
    re-run does not cover it.

## Change log

- 2026-10-08: created (Quick POC).
- 2026-10-08: added the label sweep to Open items (user decision: log1p
  default, sweep in modeling, model and loss follow the label).
- 2026-10-08: "cold" split into an age axis (new) and a traffic axis
  (dormant, long-tail, torso, head), on the query and item sides (PRD
  Slices). Complexity gate and label sweep now use new and long-tail. The
  exploration slot is for new pages only. Added per-day counts as a
  feature.
- 2026-10-09: V1 now assumes the text, embedding and structure features
  and candidate sources (user decision), with the pipeline, model and
  cost. The proxy can't measure them yet.
- 2026-10-09: complexity gate changed to per-slice routing (user decision
  after the train step): the model ranks only the slices where it beats V0
  with a CI above 0; new pages are also judged on candidate recall.
- 2026-10-09: added the item-side new-page guardrail after the test
  evaluation (a click-trained model shows new pages less often than V0).
