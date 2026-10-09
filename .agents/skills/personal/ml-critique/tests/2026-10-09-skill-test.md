# Test: ml-critique skill series, ADR 0018 changes

Contents: Setup | Changes to older tests | Tests | Results

Note (ADR 0020): Quick mode is removed. T5-T7 test Quick mode and stay as
history. The merge and share-out skills are tested in
`2026-10-09-merge-share-out-test.md`.

Date: 2026-10-09. Skills under test: `ml-critique`, `ml-critique-system`,
`ml-critique-modeling`, `ml-playbooks.md`, and
`ml-critique/references/coverage.md`. Reason for this file: ADR 0018
added Quick mode, the 3 Select questions, the critique context, the sort
key, the coverage map, and the item-to-item playbook. The tests in
`2026-10-08-skill-test.md` (T1-T4) do not cover them.

## Setup

- Run each test in a new session, so that the skill text is the only
  guide. The session that wrote the skill knows too much.
- Run on scratch copies in the session scratchpad (`critique-test/`). The
  real `labs/` folders do not change.
- Record a checksum of each input file before the run
  (`shasum -a 256`). Compare after the run.
- **Simulated user.** Select and Converge need user answers. Use the
  scripted answers in each test, written before the run.

```
T5 Select questions (no files needed past Select)
T6 Quick + context, mixed file ----> Riot interview report copy
T7 Context conflicts --------------> small write-up + scripted context
T8 Coverage, planted gaps ---------> copy of ml-riot-wiki-recommender-1
```

## Changes to older tests

- T1 in `2026-10-08-skill-test.md` tests "Brief" mode. Read it as Quick
  mode. Its criterion 9 ("no new commands are run") is replaced: Quick
  allows one probe, only for a P1 that needs proof.
- T4 criterion 2 lists the old sections. The current list adds Context
  after Summary, and in Quick mode Appendix and Not checked before
  Conclusion.

## Tests

### T5: Select asks 3 questions and waits

- Input: each prompt below, with a copy of
  `labs/ml-riot-wiki-recommender-1/interview/original-design-to-review.md`.
  1. "critique this report" (no mode keyword)
  2. "quick critique of this report"
  3. "full critique of this report, compare with nothing"
- Answer key:
  1. Asks mode, view, and context in one message.
  2. Asks view and context only (the keyword selected Quick).
  3. Asks context only, or asks view and context. The words "compare with
     nothing" may answer the view; the skill must not assume a context.
- Pass criteria:
  1. One message holds all questions, with the lens and the problem type
     in one line.
  2. No default is assumed for the view or the context.
  3. No lens starts before the user answers.
  4. The skill does not search for a reference design.

### T6: Quick mode, mixed file, interview context

- Input: the report copy from T5. Scripted answers: "fresh; context:
  `instructions.md`" (a copy of
  `labs/ml-riot-wiki-recommender-1/interview/instructions.md`).
- Answer key (not given to the lenses):
  - **K1, split.** A random 80/20 split of click pairs puts the same
    articles and pairs in train and test. Expected: P1 (modeling C1, B4;
    playbook item-to-item).
  - **K2, metric.** AUC and accuracy on 1:4 random negatives; Precision@5
    0.31 is waved away. Expected: P1 (modeling I1, I11; system B2, B5).
  - **K3, baseline.** No untrained TF-IDF cosine or co-click baseline.
    Expected: P1 (modeling A2; system G1; playbook item-to-item).
  - **K4, overfit.** Train AUC 0.97 against test 0.88 is not discussed.
    Expected: P2 or P1 (modeling I8).
  - **K5, cold start.** New articles get no embedding update for up to a
    week, and articles with no clicks train little. Expected: P2 (system
    E6; playbook item-to-item).
- Pass criteria:
  1. Both lenses run (the file has design and results content).
  2. The item-to-item playbook variant is used: at least K1 and K3 cite
     it.
  3. K1, K2, and K3 are P1 and are in the top changes. K4 and K5
     are found (part 2, part 3, or Appendix).
  4. Findings are sorted with the sort key: no P2 before a P1.
  5. The file has Summary (view "fresh", context named), Context, the 4
     parts, Decisions and trade-offs, Deferred, Appendix, Not checked,
     and Conclusion. `check_doc.py` with the Quick `--sections` prints
     `OK`.
  6. The Context section names `instructions.md`. Its 4 required topics
     match the 4 parts, so the section lists no conflict for them.
  7. Wall-clock time from the first message to the written file is 2
     hours or less.
  8. The write-up files did not change.

### T7: Context conflicts are noted; no context uses general rules

- Input: a 1-page design write-up (any fixed text, made before the run).
- Run A, Normal mode. Scripted context: "List all findings as one flat
  list with no priorities. Finish in 30 minutes. Add a one-paragraph
  summary for a manager."
- Answer key (Run A):
  - Conflict 1: one flat list with no priorities, against the sort key
    and the 4 parts. Expected: the context wins, and the conflict is
    noted.
  - Conflict 2: 30 minutes, against Normal mode with no limit. Expected:
    the context wins, and the conflict is noted.
  - Not a conflict: the manager summary is an addition. Expected: done,
    with no conflict note.
- Run B, Normal mode. Scripted context: "none".
- Pass criteria:
  1. Run A: each conflict is said in chat when it changes the work, and
     is in the Context section with the rule, the context requirement,
     and what was done.
  2. Run A: the manager summary is present and is not listed as a
     conflict.
  3. Run A: the lenses received the context (it appears in their
     returned conflicts or output).
  4. Run B: the Context section says "none (general rules)". Findings are
     sorted with the sort key, in the 4 parts.

### T8: Normal mode covers the new catalog items

- Input: a copy of `labs/ml-riot-wiki-recommender-1` with these parts
  removed before the run (the answer key, not given to the lenses):
  - **G1, team.** The PRD Team section (stakeholders, dependencies,
    reuse). Expected: system C7.
  - **G2, features.** The feature list in `design/`. Expected: system
    G1a.
  - **G3, test plan.** The test plan and CI/CD lines in the delivery doc.
    Expected: system I10.
  - **G4, democratize.** The reuse part of post-delivery. Expected:
    system J6.
  - **G5, profile.** The profile section of `modeling/01-data.md`.
    Expected: modeling B8.
- Run A: Normal mode, both lenses, fresh view, no context.
- Run B: Quick mode, same input.
- Pass criteria:
  1. Run A finds G1-G5, each with its catalog ID and an alternative.
  2. Run A: each finding has a priority, and the parts are sorted with
     the sort key.
  3. Run B: each of G1-G5 is found, in the Appendix, or its catalog item
     is in Not checked. None is silently absent.
  4. The coverage map check passes before the run: each ID in
     `coverage.md` exists in a catalog, and each catalog ID has a row.

## Results

Not run yet. The token cost is high, so the runs wait for the user's
go-ahead, as the D1-D3 and M1-M3 specs do.
