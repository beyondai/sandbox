# Test: ml-system-design skill series

Contents: Setup | Tests | Results

Date: 2026-10-09. Skills under test: `ml-system-design` and its section
skills (`-definition`, `-high-level`, `-delivery`). Reason for this file:
the Anthropic skill checklist asks for at least 3 evals per skill (ADR
0015).

## Setup

- Run each test in a new session, so that the skill text is the only
  guide. The session that wrote the skill knows too much.
- Run on scratch copies in the session scratchpad (`design-test/`). The
  real `labs/` folders do not change.
- Record a checksum of each input file before the run
  (`shasum -a 256`). Compare after the run.

```
D1 Triggering (no files)
D2 Definition, new topic ------> output in a new project folder
D3 Review, planted gaps -------> copy of ml-riot-wiki-recommender-1
```

## Tests

### D1: The correct skill triggers

- Input: each prompt below, in a new session. Record the skill that
  loads.
- Answer key (prompt -> expected skill):
  1. "Write the problem statement and metrics for a fraud model"
     -> `ml-system-design-definition`
  2. "Frame search ranking as an ML problem and draw the architecture"
     -> `ml-system-design-high-level`
  3. "Which loss and negatives for a two-tower retrieval model?"
     -> `ml-system-design-deep-dive`
  4. "Plan the A/B test and the kill switch for the new ranker"
     -> `ml-system-design-delivery`
  5. "Add SHAP and a V2 roadmap to the design doc"
     -> `ml-system-design-post-delivery`
  6. "Write a full ML design doc for ad click prediction"
     -> `ml-system-design`
  7. "Critique this design doc" -> `ml-critique`
  8. "Fix the flaky unit test in utils.py" -> no `ml-*` skill
- Pass criteria:
  1. At least 7 of 8 prompts load the expected skill.
  2. No prompt loads `-prd`, `-monkey-mode`, or `-monkey-mlp`. They are
     manual only (`disable-model-invocation: true`).

### D2: Definition for a new topic

- Input: "Write the Definition section for a support-ticket priority
  classifier." Project folder: `labs/ml-ticket-priority-1/` in the
  scratch copy.
- Pass criteria:
  1. The file is in `<project>/design/` or `<project>/prd/`, not in
     `notes/`.
  2. It has an out-of-scope list and a baseline (never-skip items).
  3. It has offline, online, and guardrail metrics, each with a target.
  4. Scale and latency have numbers, not words such as "fast".
  5. `check_doc.py` on the file prints `OK`.

### D3: Review finds planted gaps

- Input: copy of `labs/ml-riot-wiki-recommender-1` with 2 planted gaps.
  Prompt: "Review the design docs in this project."
- Answer key (not given to the session):
  - **G1, no fallback.** Delete the fallback section from
    `design/delivery.md`. Expected: flagged as a never-skip item.
  - **G2, no phasing.** Delete the V0/V1/V2 phasing from
    `design/high-level.md`. Expected: flagged by the high-level
    checklist.
- Pass criteria:
  1. G1 and G2 are found. Each has `file:line` or a quote.
  2. Each finding gives what to add.
  3. The input files did not change (checksums).

## Results

Not run yet. Run each test, then write a table here: test, result
(pass or fail), and each defect. Fix the skills, then record the fixes.
