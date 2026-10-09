# Serving reference

Contents: Mode | Stages | Latency budget | Online features | Model format and
hardware | Caching | Scaling | Cost | What to record

Shared by `ml-system-design-deep-dive` (Serving item, on paper),
`ml-modeling-serve` (measured, hands-on), `ml-system-design-delivery`
(load test, monitoring), and the critique lenses. The values are starting
points. Keep the simplest serving path that meets the PRD numbers
(`ml-design-principles.md`, Principle 1).

Inputs: the PRD non-functional requirements (peak load, p99 latency,
availability, cost sensitivity) and the high-level framing (scoring
population and cadence).

## Mode

Pick by the decision cadence, not by preference.

| Mode | Use when | Example |
|---|---|---|
| Batch | The decision is scheduled, or the inputs change slower than the decision | Weekly churn list, nightly email ranking |
| Online | The input changes inside the request, or the decision is at request time | Fraud check at checkout, search ranking |
| Hybrid | Slow parts precomputed in batch, a light model online | Batch embeddings + online re-ranker |

- Batch is cheaper and simpler. Go online only when the cadence needs it.
- A batch score has an age. State the freshness that the PRD allows.

## Stages

- Small candidate set (under ~1k items per request): score all in one
  stage.
- Large catalog: retrieval (popularity, co-occurrence, or two-tower +
  ANN index) to 100-1,000 candidates, then a ranker, then business rules.
- Give the number of candidates at each stage. The ranker cost grows with
  it.

## Latency budget

- Start from the PRD p99. Divide it between the stages, with 10-20% left
  for the network and serialization.
- Example for 100 ms p99: feature fetch 15, retrieval 20, ranking 40,
  rules 5, slack 20.
- A stage over its budget: precompute, cache, a smaller model, or fewer
  candidates. Change the budget only with the PRD owner.
- Measure p99, not the mean. Tail latency decides the user experience.
- Hands-on route: step 3 (`ml-modeling-train` or `-multiagent`) records a
  rough 1-row predict time for each candidate, so a model that cannot meet
  the budget does not win. Step 5 (`ml-modeling-serve`) measures the full
  path with `bench_serve.py`.

## Online features

- Use the same feature code for training and serving
  (`modeling/features.py` `transform()`). Two implementations drift apart:
  training-serving skew.
- Slow features (counts over days, embeddings): precompute in batch, read
  from a feature store or a key-value cache at request time.
- Request features (time, device, query): compute in the request.
- Log the features that serving used, so the next training set can use
  the same values.

## Model format and hardware

- Trees and linear models: CPU. Serialize the fitted object (joblib, ONNX,
  or the native LightGBM/XGBoost format).
- Small MLPs: CPU is usually enough. Large embeddings, attention, images:
  GPU, or CPU after compression.
- Too slow: distillation to a smaller model, quantization (int8), fewer
  trees or a shallower depth, or batching requests on the server.
- Record the model size on disk and in memory.

## Caching

- Cache scores whose inputs change slower than the requests arrive. Set a
  TTL from the freshness need.
- Cache embeddings and slow features, not whole responses that depend on
  request context.
- State the expected hit rate. The capacity math uses the misses only.

## Scaling

Size for the peak, not the average.

- **Online capacity:**
  `replicas = ceil(peak QPS x (1 - cache hit rate) / QPS per replica x headroom)`.
  - QPS per replica: measured (hands-on: `bench_serve.py`) or estimated
    (paper: mark it as an assumption).
  - Headroom 1.3-1.5, for spikes and for 1 replica down.
  - Autoscale stateless model servers between the average and the peak.
- **Sharding:** when the ANN index or the embedding tables do not fit in
  the memory of 1 machine.
- **Regions:** more than 1 region only when the availability target needs
  it (for example 99.99%).
- **Batch capacity:** `job time = population / throughput (rows per
  second, for all workers)`. The job time must fit in the scoring window
  with margin (for example under 50% of the window).
- **Degradation under overload:** decide the order. Example: fewer
  candidates, then cached or popular results, then the fallback from
  Delivery.
- **Proof:** the load test in Delivery runs at the peak QPS with this
  replica count.

## Cost

- Online: cost per 1,000 predictions and per day, at peak capacity.
- Batch: cost per run and per month.
- Compare with the value of the model (PRD). Unknown prices: give the
  formula and mark the result as an assumption.

## What to record

A design doc (deep dive, Serving) and a serving report (`05-serve.md`)
state:
- the mode and the reason from the cadence;
- the stages and the candidates at each stage;
- the latency budget for each stage, and the p99 (measured or estimated);
- how online features are fetched, and that serving uses the training
  feature code;
- the model format, size, and hardware;
- the cache and its TTL, if any;
- the capacity: peak QPS, QPS per replica, replicas (or batch job time
  against the window), and the degradation order;
- the cost at peak.
