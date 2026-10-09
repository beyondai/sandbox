# Original design to review: Wiki Article Recommender

Source: `notes/mle-interview-deep-tech-riot.pdf`, pages 1-3. This is the
junior engineer's report, as given. It is not a critique. The interview
instructions are in `instructions.md`.

## Background

- Riot internal teams write post-mortems, design specs, onboarding
  guides, runbooks, and knowledge base articles.
- The internal wiki has tens of thousands of pages.
- Engineers say that they cannot find what they need.
- New hires spend a lot of time searching for docs during onboarding.
- The ML engineering team must build a recommendation system. It
  suggests relevant articles to employees, based on what they read now.

## 1. Problem statement

- Input: the article that the user views now.
- Output: 5 other articles that the user might find useful.

## 2. Dataset

- All wiki articles from the last 3 years.
- Stubs (< 50 words) are removed. Result: 42,000 articles.
- Click log: a user reads article A, then clicks through to article B.
  That is a positive signal.

Summary statistics:

- 42,000 articles
- 1.2M click-through events over 12 months
- Average article length: ~800 words
- 3,400 unique users in the click log

Split: 80/20 random, for train and test.

## 3. Approach: two-tower model

```
 Article A (text)         Article B (text)
       |                        |
  TF-IDF (50K vocab)       TF-IDF (50K vocab)
       |                        |
  Dense 512                Dense 512
  Dense 128                Dense 128
  Dense 64                 Dense 64
       |                        |
  64-dim embedding         64-dim embedding
       +-------- cosine -------+
                    |
       binary cross-entropy
       (clicked = 1, not clicked = 0)
```

- The two towers share weights.
- Input is TF-IDF vectors.
- The model learns 64-dim article embeddings.
- Training data: (article A, article B, clicked) triples.
- Negative sampling: for each positive click pair, 4 random articles are
  sampled as negatives.

Training details:

- Framework: PyTorch
- Optimizer: Adam, lr=0.001
- Batch size: 1024
- Epochs: 50
- Training time: ~2 hours on a single V100

## 4. Results

| Metric      | Train | Test |
|-------------|-------|------|
| AUC         | 0.97  | 0.88 |
| Accuracy    | 0.93  | 0.85 |
| Precision@5 | -     | 0.31 |

The author's view, as written: "We're happy with the AUC and accuracy
numbers. Precision@5 is lower, but recommendations are subjective so this
is expected."

## 5. Serving plan

- After training, precompute embeddings for all 42K articles.
- Store them in a vector database.
- At query time, look up the current article's embedding. Return the 5
  nearest neighbors by cosine similarity.
- Every week, retrain on the latest click data and recompute all
  embeddings.

## 6. Next steps (from the author)

- Deploy behind an internal API.
- Add a feedback button ("was this helpful?") to collect explicit signal.
- Explore BERT embeddings instead of TF-IDF.
