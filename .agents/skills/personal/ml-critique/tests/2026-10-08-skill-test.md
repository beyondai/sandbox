# Test: ml-critique skill series

Contents: Setup | Tests | Results

Date: 2026-10-08. Skills under test: `ml-critique`, `ml-critique-system`,
`ml-critique-modeling`, and Principle 1 in `ml-design-principles.md`.

## Setup

- All tests run on scratch copies in the session scratchpad
  (`critique-test/`). The real `labs/` folders do not change.
- The main session acts as the `ml-critique` orchestrator and follows the
  skill text. The lens and reference passes run as new subagents, as the
  skill says.
- **Simulated user.** Converge needs user answers. The test uses scripted
  answers, written before the critique runs (see T4). This tests the
  procedure, not the quality of real user decisions.

```
 T1 Brief, both lenses ----> T4 Converge + Document (scripted user)
   (riot-churn-1 copy)          |
                                +--> T3 reference design inserted in Converge
 T2 Normal, modeling lens, planted errors (kaggle-churn-1 copy)
```

## Tests

### T1: Brief mode, both lenses, real project

- Input: copy of `labs/ml-riot-churn-1` (prd, design, spec, modeling, code,
  and `monkey-mode/`).
- Pass criteria:
  1. The orchestrator asks the reference-design question once, and does not
     search for a reference.
  2. The lenses do not use `monkey-mode/` as a reference design.
  3. Only P1 and P2 findings. Maximum 3 strengths, and maximum 5 items in
     each of parts 2, 3, and 4.
  4. Each part is in priority order. Upstream items come first.
  5. The output starts with the top 3 changes.
  6. Each part-2 and part-3 item has evidence (`file:line` or a quote) and
     an alternative.
  7. Part 4 has playbook questions, each with an expected answer.
  8. Principle 1 is applied (the complexity gate is examined).
  9. No new commands are run (Brief mode).

### T2: Normal mode, modeling lens, planted errors

- Input: copy of `labs/ml-kaggle-churn-1` with 3 planted errors.
- Answer key (not given to the lens):
  - **E1, target leak.** `engineer_features.py` builds `contract_end_flag`
    from `Churn`. `02-features.md` describes it as a billing flag.
    Expected: P1, with command output that proves the leak.
  - **E2, complexity gate.** `03-train.md` selects a stacked ensemble
    (RF + HGB + MLP) for +0.0003 AUC (inside the noise, std 0.0007), at
    22 times the training time and with a GPU. Expected: P2 (Principle
    1, catalog F4). The alternative: keep `hist_gradient_boosting`.
  - **E3, metric.** `04-evaluate.md` makes accuracy at the 0.5 threshold
    the primary metric. The PRD names AUC-ROC. Expected: P1 or P2
    (catalog I1, I2, I3).
- Pass criteria: all 3 errors found with the expected priority. E1 has
  command output. Each has an alternative. Normal mode does not limit the
  number of findings.

### T3: Reference design inserted during Converge

- Input: the T1 critique, then the user gives
  `monkey-mode/report.md` as the reference design after round 1.
- Pass criteria:
  1. The lens does not run again. A separate reference-pass subagent runs.
  2. The new items have the `[ref]` tag and are put in priority order.
  3. The reference is judged, not copied: at least one point where the
     write-up is better, or one judgment-difference question.
  4. If a `[ref]` P1 contradicts a resolved decision, the orchestrator
     asks to reopen it.

### T4: Converge and Document, scripted user

- Input: the T1 critique (and T3 items).
- Scripted answers, fixed before the run:
  - Round 1: accept the first P1 item, modify the second item (with a
    stated change), reject the third item (with a reason), defer the
    fourth item (owner: "data team", unblock: "label table rebuilt").
    Accept all other round-1 items.
  - Round 2: accept all.
- Pass criteria:
  1. Maximum 2 rounds of 6 or fewer questions, P1 first.
  2. The output file has the sections in order: Summary (top 3 changes,
     reference named), Done well, Change or fix, Missing, Questions,
     Decisions and trade-offs, Deferred, Conclusion.
  3. Each decision has a trade-off. Each deferred item has a reason, owner,
     unblock condition, and risk.
  4. The conclusion has a verdict.
  5. The write-up files did not change.

## Results

Outputs are in the scratchpad `critique-test/out/` (lens results),
`critique-test/probes/` (T2 probe scripts), and
`critique-test/ml-riot-churn-1/critique/2026-10-08-both.md` (T4 file).
The scratchpad is temporary.

| Test | Result |
|---|---|
| T1 | Pass, with 4 defects (fixed, see below) |
| T2 | Pass: 3 of 3 planted errors found |
| T3 | Pass for criteria 1-3. Criterion 4 not triggered. |
| T4 | Pass |

### T1: Brief mode, both lenses

- Pass: caps for each lens, P1 and P2 only, evidence and an alternative on
  each item, expected answers on each question, Principle 1 applied (C5a
  and G2a for system, F4 for modeling: the random forest gain +0.0009 AUC
  is inside std 0.005).
- Pass: no reference design used. Both lenses state that they did not open
  `monkey-mode/`. No analysis commands were run.
- Strong findings: the scoring population includes players who already
  left (precision@20% = 0.997), the action does not match the scored
  population, and the label comes from a synthetic column.
- Defects found:
  1. **Merged caps can remove a P1.** The caps were defined for each part,
     but not for 2 merged lenses. The merged part 2 had more than 5 P1
     items.
  2. **Brief "[C] only" is too strict.** The modeling lens correctly kept a
     non-[C] bug: `fillna(0)` makes recency 0 mean "active today".
  3. **A top-3 item held 3 changes** (label, split, and metric in one
     item).
  4. **"Upstream" was not defined.** The system lens put framing (D)
     before metrics (B).

### T2: Normal mode, planted errors

| Planted error | Expected | Found |
|---|---|---|
| E1 target leak | P1, command evidence | P1 (2.1). Probes: the flag is 1 for 100% of churners; AUC 0.9155 -> 0.9390 with the flag; KeyError on Kaggle test.csv. |
| E2 complex model in the noise | P2, Principle 1 | P2 (2.3). +0.0003 = 0.52x the fold std; alternative: HGB with a cost table. |
| E3 accuracy as primary | P1 or P2 | P1 (2.2). Conflicts with the PRD and `04-evaluate.json`. |

- It also found real issues: the probabilities are not calibrated (mean
  score 0.351 against a prevalence of 0.225, and the PRD asks for
  calibration), and the baseline is weak (LR 0.9084, so the true lift is
  +0.0071, not +0.0106).
- No limit on findings in Normal mode (9 changes, 6 missing items, 7
  questions). Probes ran in the scratchpad.

### T3: Reference design during Converge

- Pass: the lenses did not run again. A separate reference pass ran, and
  its items have the `[ref]` tag.
- Pass: the reference was judged, not copied. The write-up is better on
  2 points. The reference is better on 1 point (the recency fill). The
  pass found that the write-up copied a weak success bar from the
  reference (C6, P2).
- Not tested: no `[ref]` P1 contradicted a decision, so the reopen
  question did not happen. A later test needs a reference with a P1
  contradiction.

### T4: Converge and Document

- Pass: 2 rounds of 6 questions, P1 first. All 4 resolution types were
  recorded.
- Pass: the file has 8 sections in order, 0 lines over 80 columns, a
  trade-off for each decision, and a reason, owner, unblock condition,
  and risk for each deferred item. Verdict: needs rework.
- Pass: the checksums show that no input file changed (T1 to T4).

### Fixes applied to the skills

1. A limit never removes a P1. The limits apply to the merged result. The
   P2 items that a limit removes are listed in one line under their part.
2. Brief mode checks `[C]` items, and also keeps any P1 or P2 that the
   reviewer finds while reading.
3. Each top-3 change is a single change.
4. Upstream order = the lens catalog's section order.

### Limits of this test

- Scripted user answers test the procedure, not real decisions.
- The orchestrator was the same session that designed the skill. A cold
  run in a new session is a stronger test.
- The Brief time limit (45 minutes) was not measured. T1 used about 3
  minutes for each lens. Converge time depends on the user.
- The T2 leak was planted, so detection is expected. The 2 real findings
  (calibration and weak baseline) are better evidence of quality.
