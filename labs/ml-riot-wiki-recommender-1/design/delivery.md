# Delivery: Riot wiki article recommender

- Mode: Quick POC (2026-10-09). Items marked **(assumption)** are the most
  likely answer, not confirmed by the user.
- Inputs:
  - `prd/riot-wiki-article-recommender.md` (Baseline, Metrics - online,
    non-functional requirements);
  - `design/high-level.md` (Phasing, V1 gate, guardrail);
  - `modeling/04-evaluate.md` (offline results, hands-on route);
  - `modeling/05-serve.md` and `05-serve.json` (serving design and
    capacity).
- Proxy rule: the offline numbers come from the Wikipedia proxy. They show
  the method works; Riot numbers replace them once Riot logs exist.

## Fallback

Every failure has a named trigger and a named target. The default target
is the PRD baseline, the **V0 rule**: opened-next popularity, with empty
slots filled by the day-one rule (out-links + back-links + page-tree
siblings, ranked by 30-day views).

```
failure                          trigger                        target
model worse than V0              registration gate fails        keep last model
model worse online               guardrail breach (below)       V0 for all slices
nightly batch fails              job error or no write by 06:00  last good batch
2 nights without a batch         alert                          V0 rule batch
page not in the KV store         KV miss                        day-one rule
overload                         p99 > 150 ms for 5 min         degradation order
permission leak                  any leak in the audit          panel off (kill switch)
Recs API down                    health check fails             panel hidden
```

- **V0 is always computed.** The nightly job writes two rankings to the KV
  store: `recs_v1[A]` and `recs_v0[A]`. A config flag per query slice
  picks which one the API reads. Switching back to V0 is a flag change,
  with no redeploy and no recompute. It takes effect on the next request.
- **Model regression (offline).** The weekly training registers a new
  model only if it passes the V1 gate on the last held-out window (per
  slice, CI above 0, item-side new-page guardrail). Otherwise the previous
  model stays.
- **Model regression (online).** Target V0 for all slices when, over a
  7-day window against the V0 holdback (5% of users):
  - useful-click rate drops by more than 10% relative; or
  - bounce-back rate rises by more than 20% relative; or
  - the share of new pages shown drops below the V0 holdback.
- **Batch failure.** Serve the last good batch (scores one day old, within
  the PRD's 24-hour freshness). After 2 missed nights, switch the flag to
  `recs_v0`, which a separate, simpler job writes.
- **KV miss** (a page created since the last batch): run the day-one rule
  on request (index reads, no model, 40 ms budget, `05-serve.md`).
- **Overload:** the degradation order from `05-serve.md`: drop the
  exploration slot, then serve the space's most-read pages on a KV miss,
  then the last good batch, then hide the panel.
- **Permission leak:** turn the panel off for everyone at once (kill
  switch), page the on-call, fix, then re-enable after an audit with 0
  leaks.

## Execution

Start date 2026-10-19 (assumption). Headcount from the Phasing: 1-2 MLE,
0.5 backend engineer, wiki UI support.

```
Oct 19 ---- Nov 27 -- Dec 14 | freeze | Jan 5 ------- Feb 26 -- Mar 20 ---- May 15
  M1 data+logging   M2 V0      Dec 18-   M4 V1 build        M5 V1   M6 V2
  M2 V0 build       launch     Jan 4     (needs 4 wks       test +  session +
                    A/B                  of panel logs)     ramp    exploration
```

- **M1 - data access and logging** (Oct 19 - Nov 6): read access to
  `wiki.pages`, `wiki.links`, `wiki.permissions`, `wiki.page_views` with
  session id and referrer; the impression and click log schema; the
  permission-filter library with tests. Blocking dependency: the wiki
  platform team (PRD, Team).
- **M2 - V0 build** (Oct 26 - Nov 27): the nightly job (candidate rules,
  V0 rule, KV write), the Recs API, the panel UI behind a flag, the judged
  set of 200 seed pages (PRD offline metric before logs exist).
- **M3 - V0 launch** (Dec 1 - Dec 14): ramp and A/B (Deployment, Eval).
  100% by Dec 14 if the guardrails hold.
- **Holiday freeze** (Dec 18 - Jan 4, assumption): no ramps or model
  changes. Logs keep collecting.
- **M4 - V1 build** (Jan 5 - Feb 26): the text pipeline (lead text,
  TF-IDF, a small embedding model, entities, near-duplicate groups), the
  new candidate sources, the GBDT on `log1p(r)`, the per-slice routing,
  the weekly training with the registration gate.
- **M5 - V1 test and ramp** (Mar 2 - Mar 20): shadow, interleaving, A/B
  on guardrails, per-slice switch.
- **M6 - V2** (Mar 23 - May 15): exploration slot for new pages, session
  context. V3 starts after the privacy review (not dated here).
- **Team process:** 2-week sprints; a weekly 30-minute review with
  Developer Experience (the problem owner); a demo every sprint; each
  ramp step and model switch needs a written go/no-go in the team channel.

## Deployment

### Serving (from `modeling/05-serve.md`, not designed again here)

- Mode: nightly batch precompute of the top 20 per page into the KV
  store; the online path is a KV read plus a cached permission and status
  filter, top 5.
- Capacity: peak 50 QPS (PRD), 2 Recs API replicas (1 needed + 1 spare),
  batch ranking about 7 s for 4M pairs in a 6-hour window.

### Rollout

V0 launch (no panel today):

1. Dogfood: the ML team and the DevEx team (about 40 users), 1 week.
2. 5% of users, 3 days. Check the guardrails and the kill switch.
3. 50% of users (the A/B, Eval), 2 weeks.
4. 100%, keeping a 5% holdback with no panel for 4 more weeks
   (assumption), to measure the panel's long-term effect.

V1 over V0 (per slice):

1. Shadow: V1 writes `recs_v1[A]` nightly for 1 week; nothing served.
   Check: score distribution, routing shares, item-side new-page share
   against `recs_v0`.
2. Interleaving: team-draft interleaving of V1 and V0 for 50% of users,
   2 weeks (Eval).
3. Switch the flag per slice, as the interleaving result allows (long_tail
   and torso first, as on the proxy). Keep a 5% V0 holdback for the
   monitoring comparisons.

Each step needs 3 or more days with no guardrail breach, and a go/no-go.

### Test plan

- **Unit:**
  - feature parity: `serve.score()` equals the training-time scores on a
    fixed snapshot (as in `05-serve.md`, max difference 0);
  - the routing table, the candidate rules, near-duplicate collapse;
  - the permission filter, with fixtures for every restriction type.
- **Integration:** the nightly job end to end on a staging snapshot of
  the wiki: candidate generation -> scoring -> KV write -> API read ->
  panel; KV miss -> day-one rule; flag switch -> `recs_v0`.
- **Permission test:** synthetic restricted pages in every space type;
  requests as users with and without access. Pass: 0 leaks.
- **Load test (pass target from `05-serve.json`):**
  - 50 QPS (peak) for 30 minutes on 2 replicas: p99 under 150 ms, error
    rate under 0.1%;
  - 50 QPS with 1 replica killed: p99 under 150 ms (proves the spare);
  - 75 QPS (1.5x headroom) on 2 replicas: p99 under 150 ms, or the
    degradation order starts in the right sequence;
  - the batch job on the full 40k pages x 100 candidates: under 3 hours
    (50% of the 6-hour window); expected under 10 minutes.

### CI/CD

- Every PR: unit tests, the parity test, the permission tests.
- Model registry gate (weekly training): the V1 gate on the last
  held-out window, per slice with bootstrap CIs, plus the item-side
  new-page guardrail. Fail = the previous model stays.
- The nightly job runs in the existing batch scheduler (PRD, reuse).
- Config flags (routing per slice, kill switch, exploration slot) change
  without a deploy.

## Eval

### Offline

- **Method:** a temporal replay, as in `modeling/04-evaluate.md`:
  features from the 28 days before a cutoff T, labels (distinct readers
  who opened C right after A) from the 14 days after. Run weekly on the
  latest closed window.
- **Metrics:** nDCG@5 (primary), recall@5, `recall_w@5`, hit@5, coverage;
  per query slice (new, dormant, long_tail, torso, head) and item slice;
  candidate recall@100 per slice.
- **Before logs exist:** the judged set of 200 seed pages, nDCG@5 (PRD).
- **Proxy result** (hands-on route): the per-slice hybrid beats V0 by
  +0.0037 nDCG@5 [+0.0033, +0.0042]; wins on long_tail and torso; no gain
  on new pages; the model alone shows new pages less often (item side,
  -1.4 points). Riot numbers replace these after M4.

### Online

Two tests, because few thousand users give low power (PRD):

- **V0 launch: A/B by user** (Dec 1 - Dec 14).
  - Unit: the user (hashed id), 50/50.
  - Control has no panel, so the useful-click rate exists only in
    treatment. The decision metrics are the guardrails: total wiki page
    views per session (must not drop), page load time; plus the
    treatment's useful-click rate against a target of 3% of impressions
    (assumption).
  - Significance: two-sided Welch t-test on user-level means; a
    pre-registered non-inferiority margin of -2% for page views per
    session.
- **V1 vs V0: team-draft interleaving** (M5, 2 weeks).
  - Each panel request merges V1 and V0 rankings by team draft; a useful
    click (dwell over 30 s) credits the ranker that placed the page.
  - Metric: the share of users whose useful clicks favor V1. Significance:
    a binomial sign test over users, 95%.
  - Interleaving finds ranking differences with far fewer users than an
    A/B test; it suits the small offline lift (+0.4%).
  - Guardrails (bounce-back rate, stale-page share, duplicates in the top
    5, permission leaks) are compared with the 5% V0 holdback.
- **Power (assumption):** about 3,000 active users, 1,500 per arm, about
  30 panel impressions per user per day. With a user-level useful-click
  rate of 3% (standard deviation 2% across users), 2 weeks detect about a
  7% relative change in the A/B (80% power, alpha 0.05). The V1 offline
  lift is far smaller, so V1 is judged by interleaving, not by the A/B.
- **New pages:** report "days to first useful click" for pages created
  during the test, V1 against V0 (online slice for the item side).

## Monitoring

One live dashboard on the existing internal dashboard tool (assumption),
with alerts to the team's on-call channel. Latency thresholds start from
the stage budgets in `05-serve.md`.

### System health

- Recs API p99 latency: alert over 150 ms for 5 minutes (PRD target).
- Stage p99: KV read over 10 ms; permission check over 50 ms; status
  check over 10 ms (budgets). Alert after 15 minutes.
- Error rate (5xx and timeouts): alert over 1% for 5 minutes.
- Availability: 99.5% a month (PRD); alert when the monthly error budget
  is 50% used.
- KV miss rate: alert over 2% of requests (more than the new pages since
  the last batch).
- Panel shows fewer than 5 pages: alert over 5% of impressions.
- Nightly batch: success flag; duration over 1 hour (expected 10
  minutes); rows written within 10% of the expected count; no write by
  06:00 = alert; 2 missed nights = page.
- **Permission leaks:** a daily audit re-checks a sample of 10k served
  (viewer, page) pairs against `wiki.permissions`. Any leak = page the
  on-call and turn the kill switch.

### Model health

- Score distribution: PSI over 0.2 against the training distribution,
  weekly.
- Feature drift: PSI over 0.2 for the top features (`log_n_ac`,
  `log_n_ca`, `p_a_given_c`, `log_views_c`; the text features once live),
  weekly.
- Routing shares: the share of source pages in each slice moves by more
  than 20% relative week over week (for example a wiki migration that
  makes many pages look new).
- Item side: the share of new pages among served recommendations falls
  below the V0 holdback (the design guardrail).
- Offline replay (weekly): nDCG@5 per slice below the V0 rankings on the
  same window, or candidate recall per slice down more than 10% relative.
- Online (daily, 7-day rolling, against the V0 holdback): useful-click
  rate down more than 10% relative; bounce-back rate up more than 20%
  relative; duplicates in the top 5 over 2%; stale pages (not edited in 2
  years, assumption) over 5% of recommendations.
- Each model-health breach starts the "model worse online" fallback
  review; two consecutive weekly breaches switch to V0 automatically.

## Open items

- **ADRs recorded:**
  - `adr/0001-nightly-batch-with-serve-time-permissions.md`;
  - `adr/0002-v0-always-computed-per-slice-flag.md` (the fallback
    mechanism).
- The online power numbers are assumptions. Check them with the first
  2 weeks of V0 logs (users, impressions, useful-click rate and its
  spread) before M5.

## Change log

- 2026-10-09: created (Quick POC).
- 2026-10-09: both ADR candidates recorded as `adr/0001` and `adr/0002`.
