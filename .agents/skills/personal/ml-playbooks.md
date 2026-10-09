# Problem-type playbooks

The reviewer's experience, one playbook for each problem type. Shared by
`ml-critique*` and by `ml-system-design-definition` (the Baseline item). Each playbook
has the same 8 parts:

1. **Framing**: the standard ML task and label.
2. **Architecture**: the standard system shape.
3. **Baseline**: the strong simple baseline to beat.
4. **Features**: the typical strong features.
5. **Model and loss**: the usual model family and objective.
6. **Metrics**: the correct offline and online metrics.
7. **Classic mistakes**: each with its standard fix. Brief mode always runs
   these.
8. **Questions to ask**: each with the expected answer. Part 4 of the
   critique uses these.

Contents:
- [Churn and retention](#churn-and-retention)
- [Recommendation](#recommendation)
- [Search ranking](#search-ranking)
- [Fraud and risk](#fraud-and-risk)
- [Ads CTR and CVR](#ads-ctr-and-cvr)
- [Forecasting](#forecasting)
- [LTV regression](#ltv-regression)
- [NLP, LLM classification, and RAG](#nlp-llm-classification-and-rag)

---

## Churn and retention

1. **Framing.** Binary classification: "does the user become inactive in
   the next H days, at the snapshot date T?" If an intervention follows the
   score, the true goal is uplift: "does the intervention change the
   outcome for this user?"
2. **Architecture.** Batch scoring on a daily or weekly snapshot. A feature
   table with one row for each (user, snapshot date). Scores go to a CRM or
   campaign tool. A holdout group gets no intervention.
3. **Baseline.** Recency rule ("no activity for N days"), then logistic
   regression on RFM features.
4. **Features.** Recency, frequency, and monetary value (RFM). Activity
   trends (last 7 days against last 28 days). Tenure. Session length.
   Content or feature breadth. Payment events. Support tickets. Social
   connections.
5. **Model and loss.** GBDT with log loss. For uplift: a T-learner,
   X-learner, or uplift trees, trained on randomized campaign data.
6. **Metrics.** Offline: PR-AUC, recall and precision at the contact
   capacity (top k%), calibration. Online: retention rate of the treated
   group against the holdout group, incremental retained users, campaign
   cost.
7. **Classic mistakes.**
   - Label definition leaks the future: "inactive" is measured over a
     window that overlaps the features. Fix: features end at T, the label
     window starts after T.
   - Propensity is used for targeting. The model finds users who leave
     whatever you do. Fix: uplift modeling, or at least a randomized
     holdout to measure the incremental effect.
   - Already churned users are in the scoring population. Fix: score only
     users active in the last N days at T.
   - Random split on rows from many snapshots. The same user is in train
     and test. Fix: time-based split by snapshot date, grouped by user.
   - Accuracy or ROC-AUC on a 3% positive rate. Fix: PR-AUC and recall at
     capacity.
   - Users who got a past campaign are in the training data with no flag.
     Fix: remove them, or add a treatment feature.
   - The horizon is shorter than the time the team needs to act. Fix: align
     H with the campaign lead time.
8. **Questions to ask.**
   - What action follows the score, and how many users can it reach?
     Expected: a fixed capacity, usually 1% to 10%. The metric is precision
     or recall at that capacity.
   - How long does the action take to have an effect? Expected: days to
     weeks. The horizon must be longer than this time.
   - Is there a randomized holdout from past campaigns? Expected: if yes,
     use it for uplift. If no, add a holdout to the first launch.
   - What is "churn" in a non-subscription product? Expected: no activity
     for a window that covers 90% or more of normal gaps between sessions.

## Recommendation

1. **Framing.** Rank items for a user in a context. Label: an implicit
   signal (click, play, purchase, watch time) with a defined window. Often
   multi-task: click and a deeper engagement signal.
2. **Architecture.** 2 or 3 stages: candidate retrieval (two-tower model,
   ANN index, co-occurrence, popular items), then ranking (a GBDT or deep
   model with rich features), then re-ranking (diversity, business rules).
   Embeddings and item features are precomputed. A feature store gives
   real-time user features.
3. **Baseline.** Popularity (global, and for each segment), "more like the
   last item", item-item co-occurrence.
4. **Features.** User history embeddings, item embeddings, user-item
   affinity (past interactions with the same artist, category, or
   creator), item popularity and freshness, context (time, device,
   surface), position.
5. **Model and loss.** Retrieval: two-tower model with sampled softmax or
   in-batch negatives. Ranking: GBDT or DNN (DCN, DeepFM, DLRM), with
   pointwise log loss or a pairwise or listwise ranking loss.
6. **Metrics.** Offline: recall@k for retrieval, nDCG@k, MAP, or AUC for
   ranking, coverage, diversity. Online: CTR, engagement time, conversion,
   retention, and a long-term guardrail (return visits).
7. **Classic mistakes.**
   - Position bias in the training data. Top items get clicks because they
     are on top. Fix: position as a training feature with a fixed value at
     serving, or inverse propensity weights, or randomized exploration
     data.
   - One stage for a large catalog. The latency is too high. Fix:
     retrieval then ranking.
   - Random negatives only. The model learns to reject easy items. Fix:
     add hard negatives (impressed but not clicked), and correct for
     sampling.
   - Random split leaks future interactions. Fix: time-based split. Train
     on the past, evaluate on the next period.
   - Cold start is not planned. Fix: content features, popular items by
     segment, exploration slots.
   - Feedback loop: the model only learns from what it showed. Fix:
     exploration traffic (epsilon or Thompson sampling) and logged
     propensities.
   - Optimize clicks only. Clickbait increases. Fix: a deeper engagement
     label or multi-task loss, and a long-term guardrail.
8. **Questions to ask.**
   - How large is the catalog, and what is the latency budget? Expected:
     more than 10k items or less than 100 ms means 2 stages.
   - Which signal is the true goal: click, watch time, or purchase?
     Expected: a deeper signal than click, or a weighted combination.
   - How do new items get exposure? Expected: an exploration budget or
     content-based retrieval.
   - What are the impressions? Expected: impression logs are necessary for
     hard negatives and for position-bias correction.

## Search ranking

1. **Framing.** Learning to rank: order documents for a query. Labels from
   clicks (with bias correction), purchases, or human relevance grades.
2. **Architecture.** Query understanding (spell correction, intent,
   expansion), then retrieval (inverted index BM25 and dense vector
   retrieval, often hybrid), then a learning-to-rank model, then business
   rules.
3. **Baseline.** BM25, then BM25 with popularity boosting.
4. **Features.** Text match (BM25 for each field, exact match), semantic
   similarity, document quality and popularity, query-document click
   history, freshness, user personalization.
5. **Model and loss.** LambdaMART (GBDT) with a listwise loss is the strong
   default. Cross-encoders re-rank the top results if the latency budget
   allows it.
6. **Metrics.** Offline: nDCG@k, MRR, recall@k for retrieval. Online:
   success rate (click with long dwell, or purchase), zero-result rate,
   query reformulation rate, time to success.
7. **Classic mistakes.**
   - Clicks are used as relevance with no correction. Fix: a click model or
     inverse propensity weighting by position. Human grades for a golden
     set.
   - One model for head and tail queries with no slice analysis. Fix: report
     metrics for head, torso, and tail queries.
   - Only dense retrieval. Exact-match queries (codes, names) fail. Fix:
     hybrid lexical and dense retrieval.
   - No query understanding. Fix: spell correction and synonyms before
     ranking.
   - Pointwise loss for a ranking task. Fix: pairwise or listwise loss.
8. **Questions to ask.**
   - What is the query distribution? Expected: a long tail. Most unique
     queries are rare, so tail behavior is important.
   - Is there a human-graded set? Expected: a few thousand graded pairs for
     offline evaluation.
   - What is a successful search? Expected: a click with dwell longer than
     a threshold, or a conversion. Not only a click.

## Fraud and risk

1. **Framing.** Binary classification for each event (transaction, signup,
   login), at decision time. Labels come from chargebacks, reviews, or
   reports, with a delay.
2. **Architecture.** Real-time scoring in the request path, with a strict
   latency budget. A rules engine and a model in a cascade. Actions by
   score band: allow, step-up verification, manual review, block. A
   feedback path from reviews and chargebacks.
3. **Baseline.** The current rules engine. A velocity rule (too many events
   in a short time).
4. **Features.** Velocity counters (events for each user, card, device, IP
   in 1 h, 24 h, 7 d), device and network fingerprints, account age,
   deviation from the user's usual behavior, graph features (shared
   devices, shared cards).
5. **Model and loss.** GBDT with log loss and class weights. Graph models
   for fraud rings. Anomaly detection for new patterns.
6. **Metrics.** Offline: recall at a fixed false-positive rate, PR-AUC,
   fraud amount caught (value weighted). Online: fraud loss rate, false
   decline rate, review queue size, customer friction.
7. **Classic mistakes.**
   - Label delay is not handled. Recent events look clean because their
     chargebacks did not arrive yet. Fix: a label maturity window. Train
     only on events older than the delay.
   - Rejected traffic has no labels. The model only learns from approved
     events (selective labels). Fix: a small random allow sample, or reject
     inference.
   - Velocity features computed in batch but needed in real time. Fix: a
     streaming feature store with the same logic offline and online.
   - Random split. The same fraud ring is in train and test. Fix: time
     split, and group by account or device.
   - The model is static. Fraudsters adapt within weeks. Fix: frequent
     retraining, drift monitoring, and rules for fast reaction.
   - All errors have the same cost. Fix: a cost matrix. A missed large
     fraud costs much more than a false decline on a small transaction.
8. **Questions to ask.**
   - How long until a label is final? Expected: 30 to 90 days for
     chargebacks.
   - What actions exist other than block? Expected: step-up verification
     and manual review. The model needs score bands, not one threshold.
   - What is the review capacity? Expected: a fixed number for each day.
     This sets the review band.
   - What is the cost of a false decline? Expected: lost revenue and lost
     customers. Often larger than the fraud loss.

## Ads CTR and CVR

1. **Framing.** Predict the probability of click (CTR) and conversion
   (CVR) for each impression. The auction uses the probabilities, so they
   must be calibrated.
2. **Architecture.** Real-time scoring of candidate ads at very high QPS.
   Auction: bid times predicted probability. Online learning or frequent
   retraining.
3. **Baseline.** Historical CTR for each ad and placement, with smoothing.
4. **Features.** Ad, advertiser, and campaign IDs (high cardinality),
   user features, context (placement, time, device), cross features.
5. **Model and loss.** Logistic regression with hashed crosses, or deep CTR
   models (DeepFM, DCN, DLRM) with log loss.
6. **Metrics.** Offline: log loss, normalized entropy, calibration (predicted
   against observed CTR), AUC. Online: revenue, advertiser ROI, user
   experience guardrails.
7. **Classic mistakes.**
   - Only AUC is reported. The auction needs calibrated values. Fix: log
     loss, calibration plots, isotonic or Platt calibration.
   - Negative down-sampling with no correction. Fix: correct the
     probabilities for the sampling rate.
   - Delayed conversions are labeled as negatives. Fix: a delayed-feedback
     model, or wait for an attribution window.
   - Stale model. Fix: online or daily training.
8. **Questions to ask.**
   - Does the auction use the raw probability? Expected: yes, so calibration
     is a must.
   - What is the conversion attribution window? Expected: hours to days. The
     labels must wait or be modeled.

## Forecasting

1. **Framing.** Predict a value for each series (store, product, region)
   for each future step, for a horizon. Often probabilistic (quantiles).
2. **Architecture.** Batch pipeline on a schedule. Backtest framework.
   Hierarchical reconciliation if forecasts must sum (store to region to
   total).
3. **Baseline.** Seasonal naive (the same period last week or last year),
   moving average, ETS or ARIMA.
4. **Features.** Lags, rolling statistics, calendar (day of week, holidays,
   events), price and promotion, weather, static series attributes.
5. **Model and loss.** A global GBDT on lag features is a strong default.
   Deep models (N-BEATS, TFT) for many series. Quantile loss for intervals.
   Tweedie or Poisson loss for intermittent demand.
6. **Metrics.** Offline: MASE or WAPE (scale-free), quantile loss, interval
   coverage, bias. Online: business cost (stock-outs, waste, staffing
   errors).
7. **Classic mistakes.**
   - Random split. Fix: rolling-origin backtest that mirrors the forecast
     schedule.
   - Features that are not known at forecast time (future weather, actual
     promotions). Fix: use only values known at the origin, or forecasts of
     them.
   - MAPE on series with zeros. Fix: MASE, WAPE, or sMAPE.
   - No comparison with seasonal naive. Fix: report skill against it.
   - Point forecasts when the decision needs a quantile (stock level). Fix:
     quantile forecasts tied to the service level.
8. **Questions to ask.**
   - What decision uses the forecast, and what horizon does it need?
     Expected: it sets the horizon and the quantile.
   - Must the forecasts add up across a hierarchy? Expected: often yes.
     Plan reconciliation.
   - How many series are new or intermittent? Expected: a cold-start or
     intermittent-demand method is necessary.

## LTV regression

1. **Framing.** Predict the value of a user over a horizon (for example
   90 or 365 days) from early signals (for example the first 7 days).
2. **Architecture.** Batch scoring after an early window. Scores go to
   marketing bids or user acquisition decisions.
3. **Baseline.** The average LTV for each acquisition channel and country.
   Early revenue times a fixed multiplier.
4. **Features.** Early revenue and engagement, acquisition channel,
   campaign, country, device, first-session behavior.
5. **Model and loss.** A 2-part model (probability to pay, then amount if
   paying), or a zero-inflated lognormal (ZILN) loss, or Tweedie loss. GBDT
   is a strong default.
6. **Metrics.** Offline: normalized Gini, decile calibration (predicted
   against actual for each decile), error on the total for each cohort.
   Online: ROAS of the campaigns that use the predictions.
7. **Classic mistakes.**
   - MSE on a heavy-tailed target. A few whales control the model. Fix:
     ZILN, Tweedie, or a 2-part model. Evaluate with Gini and decile
     calibration.
   - Training on cohorts whose horizon is not complete. Fix: use only
     mature cohorts.
   - Evaluation for each user when the decision is for each cohort or
     campaign. Fix: aggregate error at the decision level.
8. **Questions to ask.**
   - At which level is the decision made: user, campaign, or channel?
     Expected: campaign. Evaluate the error at that level.
   - What share of the revenue comes from the top 1% of users? Expected:
     often more than 50%. The loss must handle heavy tails.

## NLP, LLM classification, and RAG

1. **Framing.** Classification: a label for each text. RAG: answer
   questions from a document corpus with retrieval and an LLM.
2. **Architecture.** Classification: a fine-tuned encoder or an LLM with a
   prompt, with a confidence threshold and a human fallback. RAG: chunking,
   embedding, a vector index (often hybrid with BM25), a re-ranker, an LLM
   with citations, and an evaluation harness.
3. **Baseline.** Classification: TF-IDF with logistic regression, or a
   zero-shot LLM prompt. RAG: BM25 retrieval with a prompt.
4. **Features.** Text, metadata, and for RAG the chunk size, overlap, and
   document structure.
5. **Model and loss.** Fine-tuned encoder with cross-entropy, or an LLM
   with few-shot prompts. RAG: embedding model, cross-encoder re-ranker,
   generator LLM.
6. **Metrics.** Classification: macro-F1, precision and recall for each
   class, calibration. RAG: retrieval recall@k, answer faithfulness,
   answer correctness, citation accuracy, latency and cost for each query.
   Online: task success, escalation rate, user feedback.
7. **Classic mistakes.**
   - No labeled evaluation set. "It looks good" is the evaluation. Fix: a
     golden set of a few hundred examples, and an LLM judge validated
     against human labels.
   - Retrieval is not evaluated separately from generation. Fix: measure
     retrieval recall first. Most RAG failures are retrieval failures.
   - Poor chunking (fixed size across sections and tables). Fix: chunk by
     structure, and test chunk sizes.
   - No plan for prompt injection, PII, or hallucination. Fix: input and
     output guards, required citations, an "I do not know" path.
   - The cost and latency of the LLM are not in the budget. Fix: a budget
     for each query, caching, and a smaller model where it is sufficient.
8. **Questions to ask.**
   - How often does the corpus change? Expected: the index needs an update
     pipeline.
   - What is the cost of a wrong answer? Expected: it sets the abstain
     threshold and the human fallback.
   - Is there a labeled set? Expected: if no, make one before you compare
     models.
