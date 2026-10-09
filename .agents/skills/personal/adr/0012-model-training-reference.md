# One shared reference for negatives, architecture, and training setup

## Context

The `ml-*` skills told a writer to choose a model and train it. They did
not give typical options or values. 4 gaps:

- **Negatives.** Critique check G5 covered only class imbalance and
  down-sampling. No skill said how to build negatives for implicit labels
  (logs with only positives), or how to sample test negatives.
- **Architecture.** Deep-dive named model families (GBDT is the default
  for tabular data). It did not say when a cross network, a two-tower
  model, or attention pays for itself.
- **Training setup.** Train and deep-dive did not ask for the optimizer,
  learning rate, batch size, epochs, dropout, tree hyperparameters,
  hardware, or training time. A report could say "random forest with
  defaults", and nothing flagged it.
- **No common values.** Each skill that needed these facts had to restate
  them, or the model guessed them.

## Decision

```
                 ml-model-training.md
                 (negatives, architecture, NN setup,
                  tree/linear params, tuning budget,
                  what to record)
                           |
       +-------------------+--------------------+
       |                   |                    |
  design skills       modeling skills      critique lenses
  high-level:         data: build +        system G5, G5a
    architecture        record negatives   modeling B6a,
    family per phase  train, multiagent:     F2a, G5a
  deep-dive:            start from it,
    name the            record the setup
    architecture
```

1. **One reference file**: `.agents/skills/personal/ml-model-training.md`.
   It holds negative sampling types and rules, architecture choices by
   data and task, the neural network training setup, tree and linear
   hyperparameters, the tuning budget, and a "What to record" list. The
   values are starting points, not rules. The complexity gate
   (`ml-design-principles.md`, Principle 1) still applies.
2. **Skills point to it, one level deep.** High-level, deep-dive, data,
   train, multiagent, and both critique catalogs link the file. They do
   not copy its tables, so the values stay in one place.
3. **Negatives are part of the data contract.** For implicit labels,
   `ml-modeling-data` builds the negatives and records them in
   `01-data.json` as `dataset.negatives` (types, ratio, pool,
   correction). Test negatives come from the production distribution, not
   from the training negatives. Its Check step asks for both.
4. **Train records the setup.** `03-train.md` gets a "Record the training
   setup" section: hyperparameters, hardware, training time, and tuning
   budget. Multiagent candidates use the same budget and write the same
   facts to `metrics.json`.
5. **Critique checks the 3 topics.** New or changed catalog items:
   - system lens: G5 (imbalance and negative sampling), G5a (training
     setup stated);
   - modeling lens: B6a (negatives built correctly), F2a (architecture
     justified), G5a (setup and hyperparameters recorded).

## Consequences

- A design or a report that leaves out negatives, the architecture, or
  the training setup now fails a Check step or gets a critique finding.
- One file holds the typical values. Update that file when a default
  changes.
- Existing project records (for example `labs/ml-kaggle-churn-1`) do not
  have these sections. They are records, so they stay as written.
- The reference has a one-line "Contents" list, like the other files over
  100 lines (ADR 0011, step 7).
