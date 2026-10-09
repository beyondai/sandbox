---
name: ml-critique-merge
description: >-
  Merge 2 or more independent critiques of one ML write-up into one final
  critique: join the same problems, keep the stronger evidence, show and
  resolve the disagreements, keep each source's decisions and tags. Use
  when the user has several ml-critique files (or other critiques) of the
  same report and wants one final critique.
---

# ML Critique Merge

Contents: Purpose | Steps | Merge rules | Done when

## Purpose

- **Problem.** Independent critiques of one write-up (2 runs, 2 lenses run
  apart, a colleague's review) overlap and disagree. A reader cannot use
  3 lists with the same problem in different words.
- **Use** this skill to make one final critique from them, and settle each
  disagreement with the user.
- **Output.** `critique/<date>-final.md`, with the `ml-critique` sections
  plus Sources and Rejected.
- **Not here.** The share-out (what to discuss in a fixed time) is
  `ml-critique-share-out`. Do not cut items for time here.
- Uses the priority, the sort key, and the output rules of
  `../ml-critique/SKILL.md` ("Priority", step 4 "Document").
- Rationale: `../adr/0020-critique-merge-share-out-one-mode.md`.

```
 critique A --+
 critique B --+--> 1 Select --> 2 Merge --> 3 Propose --> 4 Discuss --> 5 Write --> 6 Check
 critique C --+     (context)    (join,      (sorted,      (rounds,      final.md
                                  conflicts)  questions)    until "write")
```

## Steps

Progress (copy into your reply, tick each line):

```
[ ] 1 Select: source files, critique context (ask and wait)
[ ] 2 Merge: join, evidence, disagreements, tags, decisions
[ ] 3 Propose: merged critique, top 3, disagreement questions
[ ] 4 Discuss: rounds until the user says to write
[ ] 5 Write: critique/<date>-final.md
[ ] 6 Check
```

### 1. Select

1. Find the sources: 2 or more critique files of the same write-up. A
   source can also be text that the user pastes (a colleague's review).
   If the sources review different write-ups, stop and ask.
2. Read each source from start to end. Read the write-up too, to check
   the evidence. Do not run a new critique.
3. Ask for the critique context (path, text, or "none"), unless the user
   gave one or a source names one. Use the rules in "Critique context" in
   `../ml-critique/SKILL.md`. Wait for the answer.

### 2. Merge

Apply "Merge rules" below. Make a working table: each merged item, its
source items (`A:C3`, `B:F-3`), and its status (joined, single source,
disagreement, rejected).

### 3. Propose

Show in chat:
1. The top 3 changes, selected with the sort key.
2. The 4 parts (Done well, Change or fix, Missing, Questions), sorted with
   the sort key. Give each item a new ID and its source IDs.
3. The Rejected list (one line each).
4. Each disagreement as a numbered question with your recommended
   answer and the reason. Disagreements first, P1 first.

Fit the text to the critique context (required topics, format). Do not
cut items to fit a time limit: that is the share-out's job.

### 4. Discuss

- Run rounds with the user. The user can keep, drop, move, reword, or add
  an item, change a priority, and resolve a disagreement.
- No round limit. Write nothing until the user says to write. Reason: the
  user decides when the final critique is final.
- Tag each new item that the user adds `[user]`. An item that only agrees
  with a source item gets no tag.
- If a change reopens a source decision, say so and ask.
- At the "write" request, each disagreement that is still open goes to
  Deferred with the reason "open at write".

### 5. Write

1. Write `<project-folder>/critique/<YYYY-MM-DD>-final.md`, in the folder
   of the first source. If it exists, add `-v<N>`. Never write in
   `notes/`. Use "Output docs" in `../ml-system-design/SKILL.md`.
2. Do not edit the source critiques or the write-up.
3. Sections, in this order: Summary, Sources, Context, Done well, Change or
   fix, Missing, Questions, Decisions and trade-offs, Deferred, Rejected,
   Conclusion.
   - **Summary:** the write-up, each source file, the context, the counts
     (merged items, joined, `[user]`, rejected), and the top 3 changes.
   - **Sources:** one line per source: file, view (fresh or reference),
     date, and verdict.
   - **Decisions and trade-offs:** each source decision that the merge
     kept, and each disagreement resolved in Discuss: the item, the
     decision, what was given up, and why.
   - **Rejected:** each rejected item: the item, the source, and the
     reason.
   - **Conclusion:** the verdict (`ready`, `ready with changes`, `needs
     rework`) and the top 3 changes. If the sources gave different
     verdicts, say which one the merge keeps and why.
4. In the Check, run `check_doc.py` with:

   ```
   --sections "Summary,Sources,Context,Done well,Change or fix,Missing,Questions,Decisions and trade-offs,Deferred,Rejected,Conclusion"
   ```

5. Offer `ml-critique-share-out` if the critique is for a share-out.

### 6. Check

Do "Check the output" in `../ml-system-design/SKILL.md`. Intent questions:
1. Is each source item in the file: merged, single source, or in
   Rejected? (Count the source items and the mapped items.)
2. Is each disagreement resolved in Decisions, or in Deferred with its
   reason?
3. Are the top 3 changes single changes, sorted with the sort key?
4. Are the `[user]` and `[ref]` tags kept, and is each new user item
   tagged?
5. Does the verdict follow from the decisions? Are the sources and the
   write-up unchanged?

## Merge rules

- **Same problem.** Join 2 items if they name the same defect and the
  same fix, even in different words or parts. Keep one ID. List all
  source IDs. Reason: one problem must have one decision.
- **Different fix.** If 2 items name the same defect with different fixes,
  keep one item and show both fixes as a disagreement.
- **Evidence.** Keep the stronger evidence: command output over a shown
  calculation over a `file:line` quote. Keep each calculation that a
  reader needs. Check each claim against the write-up. A claim that the
  write-up does not support goes to Rejected ("no evidence").
- **Priority.** If the sources gave different priorities, it is a
  disagreement. Recommend one with the Priority table of `ml-critique`.
- **Claims.** If the sources contradict each other on a fact or an
  inference, it is a disagreement. If one source corrected the other (for
  example a later decision), keep the correction and note it.
- **Tags.** Keep `[user]` and `[ref]` on each item that has them. A merged
  item keeps each tag of its sources.
- **Decisions.** Keep each source decision (accept, modify, reject,
  defer). If the sources decided the same item in different ways, it is a
  disagreement.
- **Rejected items.** An item that a source decision rejected leaves the
  4 parts. Put it in Rejected with the reason and the source.
- **Deferred items.** Keep each one with its reason, owner, unblock
  condition, and risk.
- **Done well.** Apply the `ml-critique` Done well rule to the merged list
  (costly to lose, at most 5). A strength that a source decision rejected
  goes to Rejected.
- **Single source.** An item that only one source has stays, with its
  source ID. Independent critiques find different things.

## Done when

1. Each source item is mapped (merged, single source, or Rejected).
2. Each disagreement is resolved or in Deferred.
3. The user said to write, and the file is written.
4. The Check passed (5 yes answers, `check_doc.py` prints `OK`), or the
   open items are reported.
5. The user confirms.
