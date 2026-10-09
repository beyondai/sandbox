Questiosn:
1: Focus on only technical design or both technical design and mock
peer design review?
2: Could be a completely new design or incremental changes or revisions
3: Communication focus on just get to the right design or coaching?
       


# Design issue noticed by reviewer without using skills



What's good:
1: Overal structure. considered full cycle
2: removed noises
3: considered negative sampling
4: documented details of the training setting, repeatable. for future check of
running variance.


What's bad
- need a reasonable baseline

- Evaluation is wrong, not AUC but should be NDCG, and recall

- approach:
  - need more features into the NN
  - need to compare TFIDF with NN and not with NN
  - should be two stage approach, retrieval and ranking
  - click label binary is wrong
  - ?is the the training details good? Need check
  - negative sampling is weak
  - ?TFIDF seems like wrong choice? why not use embeddings?
  - ?Is the NN model architecture good? should we use attention?

- Evaluation need to focus on different segments
  - head, body, tail, cold-start

- Results:
  - Evaluation is wrong
  - 0.97 vs 0.88 seems overfiting
    - reduce model complexity
    - drop out
    - L1 and L2 reg
    - early stop
    

- Serving plan:
  - update weekly is too infrequent. daily. It is cheap.




What's missing:
- key pain points: can't find, and new-hire spend too much time
  need to define metrics for these

- serving Top 5 need to add filters for access, dup, stale, self, then rank

- sliced eval:
  recall and ndcg@5 for new hires, new articles, and long-tail articles

- improvment gated update: check the updated index/rec metrics performance
  before rolling out.

Serving needs

Review's own Questions:



Transformers: pretraining, L2 weight decay, learning rate 
