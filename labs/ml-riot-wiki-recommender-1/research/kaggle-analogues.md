# Kaggle analogues for the Riot wiki recommender

Written 2026-10-08. No Kaggle competition has the exact problem: an internal
wiki, page-to-page recommendations, a 5-slot panel. These competitions each
match one part of the design.

- Sources: from memory. The links and numbers are not checked yet. Check a
  link before you cite it in a design doc.

```
our design             closest Kaggle competition
----------             --------------------------
V0 + V1 core      -->  OTTO Multi-Objective Recommender (2022-23)
product shape     -->  Outbrain Click Prediction (2016-17)
cold-start        -->  Learning Equality - Curriculum Recommendations (2023)
near-dup collapse -->  Shopee - Price Match Guarantee (2021)
V3 / V4           -->  H&M Personalized Fashion Recommendations (2022)
```

## 1. OTTO - Multi-Objective Recommender System

- Link: https://www.kaggle.com/competitions/otto-recommender-system
- **Task.** E-commerce sessions. Predict the next clicks, carts and orders.
- **Metric.** Weighted recall@20 over clicks, carts and orders.
- **Why it matches.** It is the best match for our method.
  - The winners used co-visitation counts as the candidate source. This is
    the same idea as our opened-next baseline (V0).
  - A GBDT reranker ranked the candidates. This is our V1.
  - Many public notebooks give a co-visitation-only baseline, then the
    gain from the reranker. This is the comparison that monkey-mode ran.
- **What it can test for us.**
  - The data has session ids. Wikipedia Clickstream does not.
  - So OTTO can be a second proxy for V2 (session context): recommend from
    the last 3-5 items, not only the current one.
- **Differences.**
  - Products, not documents. No text, so it can't test cold-start.
  - Data size (from memory): about 12M sessions and about 220M events.
    Check the size before a download.

## 2. Outbrain Click Prediction

- Link: https://www.kaggle.com/competitions/outbrain-click-prediction
- **Task.** A reader is on a publisher page with a "recommended content"
  widget. Predict which shown item gets the click.
- **Metric.** MAP@12.
- **Why it matches.** It is the best match for our product. The input is the
  current page, and the output is a small panel of related links.
- **What it can test for us.**
  - Learning from panel impressions and clicks. This is our feedback-loop
    problem (high-level design, "Exclusions and contamination").
  - Page context features (topics, categories, entities of the document).
- **Differences.** Paid content across many sites, not related pages inside
  one site.

## 3. Learning Equality - Curriculum Recommendations

- Link:
  https://www.kaggle.com/competitions/learning-equality-curriculum-recommendations
- **Task.** Match educational content items to topic nodes in a topic tree.
- **Metric.** F2 score.
- **Why it matches.** It is close to our cold-start problem. There are no
  clicks, only text, a tree and metadata.
- **What it can test for us.**
  - Strong solutions used embedding retrieval, then a reranker.
  - This is like the topic-similarity candidate source and the page-tree
    signals in `research/cold-start.md`.
- **Differences.** Multilingual, and the target is "belongs to this topic",
  not "useful to read next".

## 4. Shopee - Price Match Guarantee

- Link: https://www.kaggle.com/competitions/shopee-product-matching
- **Task.** Find listings for the same product from text and images.
- **Metric.** F1.
- **Why it matches.** Only the near-duplicate collapse step (cosine over
  about 0.9, one page for each group).
- **What it can test for us.** How to set the duplicate threshold. Solutions
  tuned it on labeled match groups.

## 5. H&M Personalized Fashion Recommendations

- Link:
  https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations
- **Task.** Predict each customer's purchases in the next week.
- **Metric.** MAP@12.
- **Why it matches.** Retrieve-then-rank, per user. It fits only V3 and V4
  (personalization).
- **Differences.** Purchases, not reading. No page-to-page context.

## Not Kaggle: MIND (Microsoft News Dataset)

- Link: https://msnews.github.io/
- **Task.** News recommendation from each user's click history, with article
  text.
- **Why it matches.** It has user ids and text. It is the best public proxy
  for the personalization notes (`research/personalization.md`).

## Suggested use

```
proxy                 tests                         phase
-----                 -----                         -----
Wikipedia Clickstream page-to-page, cold slice      V0, V1   (done)
OTTO                  session context               V2
MIND                  per-user personalization      V3, V4
Learning Equality     text retrieval for new pages  V1 cold-start sources
```

- Read the OTTO winning write-ups before the deep dive or `ml-modeling`.
  They are the closest worked example of our V0 -> V1 path.
- Use OTTO as a proxy only if V2 needs a hands-on test. Check the data size
  first.

## Change log

- 2026-10-08: created.
