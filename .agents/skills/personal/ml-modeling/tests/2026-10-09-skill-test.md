# Test: ml-modeling skill series

Contents: Setup | Tests | Results

Date: 2026-10-09. Skills under test: `ml-modeling-data`,
`ml-modeling-multiagent`, `ml-modeling-evaluate`, and
`ml-modeling-serve`. Reason for this file: the Anthropic skill checklist
asks for at least 3 evals per skill (ADR 0015).

## Setup

- Run each test in a new session, so that the skill text is the only
  guide.
- Run on scratch copies in the session scratchpad (`modeling-test/`).
  The real `labs/` folders do not change.
- Delete the outputs of the step under test from the copy before the
  run. Keep the outputs of the earlier steps.

```
M1 data step, planted errors ----> copy of ml-kaggle-churn-1
M2 multiagent -> evaluate -------> copy of ml-riot-wiki-recommender-1
M3 serve step -------------------> copy of ml-riot-wiki-recommender-1
```

## Tests

### M1: Data step finds and cleans planted errors

- Input: copy of `labs/ml-kaggle-churn-1`. Delete `modeling/01-data.*`.
  Plant 3 errors in the labeled table that `01-data.json` names.
- Answer key (not given to the session):
  - **E1, sentinel.** Set a numeric column to `-999` in 2% of the rows.
    Expected: flagged as sentinel-coded missing, and changed to null.
  - **E2, duplicates.** Copy 20 rows, unchanged. Expected: flagged and
    removed.
  - **E3, impossible value.** Set tenure to a negative number in 5 rows.
    Expected: flagged and cleaned, with the rule in `01-data.md`.
- Pass criteria:
  1. E1, E2, and E3 are found and cleaned. Each has a row count.
  2. `01-data.json` has the `dataset` block: table paths, label, split.
  3. The EDA notebook and the dashboard exist.
  4. `check_doc.py` on `01-data.md` prints `OK`.

### M2: The parallel route feeds the evaluate step

- Input: copy of `labs/ml-riot-wiki-recommender-1`. Delete
  `modeling/03-train.md` and `modeling/model.joblib`. Prompt: "Try 2
  models in parallel", then "evaluate".
- Reason: style guide step 2 says to check each alternative route, not
  only the default (`ml-modeling-train`).
- Pass criteria:
  1. `ml-modeling-multiagent` writes `03-train.md` and `model.joblib`.
  2. `ml-modeling-evaluate` runs with no hand fix.
  3. `03-train.md` has the table, the winner, and why it won.
  4. A complex winner passes the complexity gate
     (`ml-design-principles.md`), or the simpler model is kept.

### M3: Serve step measures, not estimates

- Input: copy of `labs/ml-riot-wiki-recommender-1`. Delete
  `modeling/05-*`. Prompt: "How do we serve this model?"
- Pass criteria:
  1. `serve.py` imports the feature code from `features.py`. It does not
     copy it.
  2. `bench_serve.py` ran, and its output is in `05-bench.json`.
  3. `05-serve.md` gives measured p50 and p99, the capacity for the peak
     load, and the cost.
  4. The mode (batch or online) agrees with `design/high-level.md`.
  5. Reference: the p50 is within 3 times the p50 in the real
     `05-bench.json` on the same machine. Reason: a larger gap means a
     different scoring path.

## Results

Not run yet. Run each test, then write a table here: test, result
(pass or fail), and each defect. Fix the skills, then record the fixes.
