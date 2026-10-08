# Personalization for the Riot wiki article recommender - design notes

Written 2026-10-08. These are design notes only. There is no POC behind them.

The V0 recommender (see the monkey-mode run in
`labs/ml-riot-wiki-recommender-1/monkey-mode/`) recommends from the current
page alone: everyone reading page A sees the same list. These notes cover what
it would take to make the list depend on who is reading. The Wikipedia
Clickstream proxy has no user ids, so none of this can be tested on it. It
needs Riot's own logs.

## Data needed

- **Per-user page-view logs.** Required for anything personal.
  - Fields: user id, page id, timestamp, dwell time, referrer (search, a wiki
    link, Slack, a Jira ticket), and session id.
  - Retention: at least 90 days, so new-hire paths can be built.
- **Org data, from HRIS/directory.** Team, role or discipline (engineer,
  designer, producer), start date (tenure), location and manager chain.
- **Page metadata.**
  - Owner team or space, created and last-edited time, and author.
  - Page type: post-mortem, design spec, onboarding guide, runbook or KB
    article.
  - Access permissions.
- **Optional, higher-effort signals.** Page edits and comments, links to wiki
  pages from Jira tickets, GitHub repos or Slack channels the user is in.
  - Strong signals, but each needs its own integration and privacy review.

## What can be done, in order of expected value

1. **Session context.** Recommend from the last 3-5 pages in the session, not
   only the current page.
   - Start simple: sum the co-visitation scores from each recent page,
     weighting recent pages more.
   - A sequence model (GRU4Rec or SASRec style) comes later, once there is
     enough session data.
   - Needs only session ids, not identity, so it is the cheapest and
     least sensitive step.
2. **Team and role affinity.**
   - "What people on your team or in your role read around this page."
   - **New-hire paths:** what people in the same role read in their first 30
     days, ordered. This targets the onboarding pain point directly.
   - Built from aggregates, not per-person history.
3. **User profile features in the reranker.**
   - A user vector = the average text embedding of pages read in the last N
     days.
   - Candidate features:
     - cosine(user vector, candidate);
     - already read (demote, or drop it unless the page was edited since);
     - owner-team match;
     - tenure bucket;
     - page freshness.
4. **Cold-start users.**
   - New hires with no history get their role or team defaults plus
     onboarding paths.
   - That is the same mechanism as step 2, so new hires are covered on day
     one.

## What to expect

- **Small data.** Riot has thousands of employees, not millions of readers.
  Most users will have tens to hundreds of page views. Per-user learned
  embeddings will be noisy.
- **Where the lift comes from.** Most of it should come from session context
  and team/role groups, not from per-user models. Plan for per-user models as
  V2 at best.
- **How big the gain is.**
  - Expect a modest gain on top of the current-page model for general browsing.
  - Expect a larger gain for new hires and for ambiguous pages (for example, a
    generic "Deploy" page means different things to different teams).
  - Measure it before committing to it.
- **Personalization narrows what people see.** Engineers partly want to find
  docs outside their team. Keep a non-personalized slot or a diversity
  constraint in the list.

## Constraints

- **Reading history is sensitive employee data.**
  - It needs HR/legal and privacy sign-off, a clear notice, and a per-user
    opt-out.
  - Set a retention limit.
- **Never expose who read what.** No "Alex read this" explanations. Use
  explanations that refer to groups: "popular with your team".
- **Minimum group size for aggregates.** A team or role aggregate needs at
  least 5 distinct readers, or it is suppressed. Otherwise it can reveal one
  person's reading.
- **Permissions.** Filter every recommendation by the viewer's access
  permissions at serve time, not only at training time.
- **Distinct users, not raw clicks.** Count users, not clicks, when building
  co-visitation, for example at least 3 different users went from A to B. One
  person refreshing a page should not create a signal.

## How to evaluate

- **Offline replay on Riot logs.**
  - Hold out the last 2 weeks.
  - For each page view, predict the next page the user opened.
  - Compare non-personalized V0, + session, and + team/role on nDCG@10 and
    recall@10.
  - Slice by tenure: new hires vs everyone else.
- **Online A/B test.**
  - Primary metric: recommendation click-through.
  - Secondary metrics: time to find a page (search-to-click time), search
    reformulation rate, and new-hire survey responses.
  - Guardrails: diversity and coverage, so the system doesn't just recommend
    each team's own pages back to it.

## Phasing

- **V0:** current page only. Click co-visitation plus text similarity for cold
  pages.
- **V1:** + session context, + team/role aggregates and new-hire paths.
- **V2:** learned user and sequence models, only if V1 logs show enough
  per-user signal to justify them.
