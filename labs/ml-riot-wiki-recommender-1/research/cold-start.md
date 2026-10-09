# Cold and new pages with no back-links - design notes

Written 2026-10-08. Agreed with the user as input for `design/high-level.md`
and the later design sections. Not yet built.

## Problem

- In the monkey-mode proxy run, candidates found only 30% of next clicks for
  cold pages (candidate click-recall 0.298). Reverse edges (back-links) gave
  almost all of that.
- A brand-new page often has no back-links and no clicks. Reverse edges can't
  help it.
- About 100 new pages a week (PRD estimate). This is a permanent load.

## Signals that exist when a page is created

```
new page (no clicks, no back-links)
 |
 |-- its own out-links ---------> linked pages + their neighbours (2-hop)
 |-- place in the page tree ----> parent, siblings, space
 |-- metadata ------------------> author, owner team, labels, template
 |-- entities in the text ------> same service / repo / Jira key / Slack channel
 '-- topic embedding -----------> similar pages (near-duplicates removed)
                                     '-> borrow their click-based recs
            |
            v
   blend -> top 5      (weight moves to click features as clicks arrive)
```

1. **Its own out-links.** Authors link to related pages (runbook, service
   page, design spec). Use those pages and their neighbours as candidates.
2. **Page tree.** Every page has a space and a parent. Siblings are often
   the same document type for the same service.
3. **Metadata.** Author, owner team, labels and template type. A
   post-mortem template points to the service runbook and earlier
   post-mortems.
4. **Shared entities.** Extract service names, repos, Jira keys and Slack
   channels from the text. Join to other pages that name the same entity.
   Expected to be the strongest logical-connection signal for internal
   docs.
5. **Topic similarity, two ways.**
   - Direct: the nearest pages by topic, with near-duplicate groups
     (cosine over about 0.9) shown as one page.
   - Borrowed clicks: take the 10 nearest warm pages. Use where their
     readers went next as candidates (content-to-behavior transfer).
6. **Fallback.** Popular pages in the same space, then curated onboarding
   pages, with diversity rules.

## The reverse problem: show the new page on other pages

- A new page has no clicks as a target, so nothing recommends it.
- Give it 1 of the 5 slots on related warm pages, chosen by the signals
  above, for a limited time (for example 2 weeks).
- Use a bandit (for example Thompson sampling). A new page with no useful
  clicks loses the slot quickly.
- This exploration slot is a permanent part of the system.

## From cold to warm

- No hard switch. The reranker already has click-count features.
- As clicks arrive, the model weights click features more and the
  structure and text signals less.

## Proxy test (not run)

- On Wikipedia Clickstream, remove all back-links and clicks for a sample
  of pages to make them look new.
- Score the cold slice at @5 with and without the out-link, entity and
  text candidate sources.
- With the saved-outputs rule, only the new candidate sources and eval need
  to run.
