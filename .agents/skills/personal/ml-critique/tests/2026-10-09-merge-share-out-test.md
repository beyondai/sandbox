# Test: ml-critique-merge and ml-critique-share-out, ADR 0020

Contents: Setup | Tests | Results

Date: 2026-10-09. Skills under test: `ml-critique-merge`,
`ml-critique-share-out`, and the `ml-critique` changes of ADR 0020 (one
mode, 2 Select questions, `[user]` tag, Done well rule). Status: specs
only, not run (evals on hold for token cost).

## Setup

- Run each test in a new session, so that the skill text is the only
  guide.
- Run on scratch copies in the session scratchpad (`critique-test/`).
  Copy `labs/ml-riot-wiki-recommender-1/critique/2026-10-09-both-v1.md`,
  `2026-10-09-both-v2.md`, and `interview/`.
- Record a checksum of each input file before the run
  (`shasum -a 256`). Compare after the run.
- **Simulated user.** Use the scripted answers in each test.

```
T9  merge v1 + v2 ---------> critique/<date>-final.md
T10 share-out, 45 minutes -> critique/<date>-share-out.md
T11 no file before "write" (both skills)
T12 ml-critique Select asks 2 questions, no Quick
```

## Tests

### T9: Merge 2 independent critiques

- Input: `/ml-critique-merge critique/2026-10-09-both-v1.md
  critique/2026-10-09-both-v2.md`. Scripted context: the copy of
  `interview/instructions.md`. Scripted Discuss: accept each recommended
  answer, then "write".
- Answer key:
  - The split, metric, and baseline findings are in both sources. Each
    becomes 1 merged item with 2 source IDs.
  - The v2 `[user]` items (2 strengths, 2 questions) keep the tag.
  - The v2 Done well rejections (D8) are in Rejected.
  - At least 1 disagreement is found (priority of the label finding, or
    a claim that v2 corrected, for example the AUC vs P@5 claim).
- Pass criteria:
  1. Each source item is mapped: merged, single source, or Rejected. The
     counts in the Summary add up.
  2. Each disagreement is asked as a question with a recommendation
     before the file is written.
  3. The file has the 11 sections; `check_doc.py --sections` prints `OK`.
  4. Done well has at most 5 items, each with what breaks if lost.
  5. The source files did not change.

### T10: Share-out fits a 45-minute interview

- Input: `/ml-critique-share-out <the T9 final.md> Context:
  interview/instructions.md`. Scripted Discuss: "move the label point
  after the split point", then "write".
- Answer key: limit 45 minutes of discussion; 4 required topics (done
  well, change or fix, missing, questions); "be ready to sketch"; type:
  working-session interview.
- Pass criteria:
  1. The timeline sums to 45 minutes or less, with about 20% free.
  2. Each of the 4 topics has at least 1 talking point.
  3. Each top 3 point has a claim, evidence, alternative, sketch, and
     2-3 follow-ups with answers.
  4. No P1 is in the Cut list while a P2 or P3 is a talking point.
  5. The scripted move is in the written order.
  6. `check_doc.py --sections` prints `OK`. The critique did not change.

### T11: Nothing is written before "write"

- Input: T9 and T10, with 2 Discuss rounds before "write".
- Pass criteria:
  1. No file appears in `critique/` before the "write" message (check
     after each round).
  2. After "write", exactly 1 new file appears for each skill.

### T12: ml-critique Select with one mode

- Input: "critique this report" with a copy of
  `interview/original-design-to-review.md`, then the same with "quick
  critique of this report".
- Pass criteria:
  1. Select asks view and context only, in one message. No mode
     question.
  2. "quick" does not limit the checks: the full catalog runs.
  3. With the interview context, the 2-hour limit is recorded in the
     Context section and is not treated as a conflict.

## Results

Not run.
