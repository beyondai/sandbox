# Model and training reference

Contents: Negative sampling | Model architecture | Neural network training
setup | Tree and linear model hyperparameters | Tuning budget | What to record

Shared by the design skills (deep-dive, high-level), the modeling skills
(data, train, multiagent), and the critique lenses. The values are
starting points, not rules: tune them on validation data, and keep the
simplest option that passes the complexity gate
(`ml-design-principles.md`, Principle 1).

## Negative sampling

Needed when the logs hold only positives (clicks, purchases, listens), or
when positives are rare and the full negative set is too large to train
on.

| Type | What it is | Use it for | Risk |
|---|---|---|---|
| Random (easy) | Uniform sample of items or rows with no positive | A first baseline; retrieval warm-up | Too easy: the model learns to reject obvious items only |
| Popularity-weighted | Sample in proportion to item frequency (often freq^0.75) | Retrieval; stops the model from just predicting "popular" | Under-samples the long tail |
| In-batch | The other positives in the same batch act as negatives | Two-tower retrieval at scale; free to compute | Popularity bias: needs logQ correction |
| Hard (strong) | Shown but not engaged (impressed, not clicked), or near misses mined by the current model (ANN neighbors, high score, label 0) | Ranking; the last quality gains | False negatives; too hard too early stalls training |
| Weak (noisy) | Unlabeled items treated as negative (never shown, so unknown) | Only when nothing better exists | Many are true positives: treat as PU learning, weight them down |
| Synthetic | Corrupted positives (swap a field, shuffle a sequence) | Contrastive or self-supervised pretraining | Can teach artifacts |

Rules:
- Mix types: a common start is random plus hard at about 1:1, with 4-10
  negatives for each positive. Add hard negatives after the model learns
  the easy ones (curriculum), because early hard negatives stall training.
- Exclude known positives of the same user from the negative pool, and
  exclude items that were not available at that time.
- Correct for sampling where scores are used as probabilities: logQ
  correction for in-batch and popularity sampling; for down-sampled
  negatives at rate r, `p = p_s / (p_s + (1 - p_s) / r)`.
- Evaluate on the production distribution (all candidates, or real
  impressions), never on the training negatives: easy negatives inflate
  offline metrics.
- Record the types, the ratio, the pool, and the correction.

## Model architecture

Start shallow. Go deeper only when the data size and the gain pay for it.

| Data and task | Start with | Deeper option, when it pays |
|---|---|---|
| Tabular, < 1M rows | Logistic/linear regression, then GBDT | Rarely: GBDT is usually best on tabular data |
| Tabular, large, many sparse ids | GBDT on counts and target encodings | Wide & Deep, DeepFM, DCN-v2 (explicit feature crosses) |
| Retrieval over a large catalog | Popularity or co-occurrence; matrix factorization | Two-tower (user and item encoders), ANN index |
| Ranking with rich features | GBDT (LambdaMART) | DNN ranker: MLP over embeddings, DCN-v2 or DeepFM for crosses |
| User behavior sequences | Recency and count features | Attention over the history (DIN), or a transformer (SASRec, BST) |
| Text | TF-IDF + linear; a frozen pretrained encoder | Fine-tuned transformer; an LLM only when the gap justifies the cost |
| Images | A frozen pretrained CNN or ViT embedding + linear | Fine-tuning |

- **MLP vs cross network vs attention.** An MLP learns feature
  interactions implicitly and needs much data to do it. A cross network
  (DCN-v2) or FM layer models pairwise crosses explicitly and is cheaper
  for the same quality. Attention pays when order or the relation between
  history items and the candidate matters (sequences, sessions).
- **Depth and width.** For an MLP head on tabular or embedding input: 2-3
  layers, widths like 256 -> 128 -> 64. More layers rarely help without
  residual connections and normalization.
- **Embeddings.** Dimension about `min(64, 1.6 * cardinality^0.56)`, or
  powers of 2 from 8 to 128. Hash or bucket very large vocabularies, and
  map rare and unseen ids to one "unknown" id.

## Neural network training setup

| Setting | Starting point | Notes |
|---|---|---|
| Framework | PyTorch | TensorFlow/Keras if the serving stack needs it; JAX for large TPU jobs |
| Optimizer | AdamW | Sparse embeddings: Adagrad or sparse Adam; SGD + momentum for some vision models |
| Learning rate | MLP/DCN 1e-3; transformer fine-tuning 2e-5 to 5e-5; from scratch 1e-4 to 3e-4 | Run a short LR range test if unsure |
| Schedule | Linear warm-up (1-5% of steps), then cosine or step decay | Constant LR plateaus early |
| Batch size | 512-4096 for tabular and recommendation; 16-64 for transformer fine-tuning | Larger batches need a larger LR; in-batch negatives improve with size |
| Epochs | Early stopping on the validation metric, patience 2-5, a cap of 20-50 | Load the best-validation weights; never select on test |
| Dropout | 0.1-0.3 in MLP layers; 0.1 in transformers | 0 for small, well-regularized models |
| Weight decay | 1e-5 to 1e-2 (AdamW) | Not on embeddings and biases |
| Normalization | BatchNorm or LayerNorm in deep MLPs; LayerNorm in transformers | Standard-scale numeric inputs |
| Loss | Matches the metric: log loss (calibrated scores), sampled softmax (retrieval), pairwise or listwise (ranking) | See the loss rules in the playbooks |
| Hardware | CPU for linear, GBDT, and MLPs under ~1M rows; GPU (or Apple MPS) for embeddings over millions of rows, attention, and images | Mixed precision (bf16/fp16) on GPU |
| Training time | Set a wall-clock budget first (POC: minutes; production: hours) | Record the real time; it is part of the running cost |
| Reproducibility | Fix the seeds; log versions | GPU kernels can still differ slightly |

## Tree and linear model hyperparameters

**Random forest** (scikit-learn names):
- `n_estimators`: 200-500. More trees never overfit; they only cost time.
  Stop when out-of-bag score stops improving.
- `max_depth`: None (full trees) to start, or 10-30 for large noisy data.
- `min_samples_leaf`: 1-5; 10-50 for noisy labels or calibrated scores.
- `max_features`: `"sqrt"` for classification, 0.33-1.0 for regression.
- `class_weight="balanced_subsample"` for imbalance; `n_jobs=-1`;
  `oob_score=True` for a free validation estimate.

**Gradient boosting** (LightGBM / XGBoost names):
- `learning_rate` 0.05-0.1, with up to 1000-5000 rounds and early
  stopping (50-100 rounds of patience) on validation.
- `num_leaves` 31-127 (LightGBM) or `max_depth` 6-8 (XGBoost).
- `min_child_samples` / `min_child_weight`: 20-100.
- `subsample` and `colsample_bytree`: 0.7-0.9.
- `reg_lambda` 0-10, `reg_alpha` 0-1.
- Imbalance: `scale_pos_weight = negatives / positives`, or tune the
  threshold instead.
- scikit-learn `HistGradientBoosting`: `max_iter` 200-1000 with
  `early_stopping=True`, `learning_rate` 0.05-0.1, `max_leaf_nodes` 31.

**Logistic / linear regression:**
- Standard-scale the inputs. Tune `C` (or `alpha`) on a log grid from
  1e-3 to 10.
- Solver: `lbfgs` (L2), `saga` (L1 or elastic net, large data);
  `class_weight="balanced"` for imbalance. Check that it converges.

## Tuning budget

- Use random search or Bayesian search (Optuna), not a full grid: 30-100
  trials for GBDT, 20-50 for a DNN. Tune the 3-4 parameters that matter
  most first (GBDT: learning rate and rounds, leaves or depth, min child
  samples; DNN: learning rate, batch size, dropout, width).
- Give each candidate the same budget and the same validation split.
- A best value at the edge of the search range means: widen the range.

## What to record

A design doc (deep dive) and a training report (`03-train.md`) state:
- the architecture and why (shallow or deep, MLP, cross network, or
  attention);
- the negative sampling plan, if any (types, ratio, pool, correction);
- the training setup: framework, optimizer, learning rate and schedule,
  batch size, epochs and early stopping, regularization (dropout, weight
  decay), or the key tree hyperparameters;
- the hardware (CPU, GPU, MPS), the training time, and the tuning budget.
