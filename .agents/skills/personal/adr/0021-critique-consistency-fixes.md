# Critique skills: share-out keeps each P1, one meaning for [C], fuller Checks

## Context

On 2026-10-09 the user asked for the skill checks on the `ml-critique*`
skills. Both scripts printed `OK`. The manual checklists found 5
problems:
1. The share-out example timeline in `docs/ML-CRITIQUE-GUIDE.md` put
   credit after the criticism. `ml-critique-share-out/references/delivery.md`
   says "credit before criticism".
2. `ml-critique-share-out` had 2 rules that can conflict with a short
   limit: each required topic gets a point, and no P1 is cut while a P2
   or P3 is in. It did not say which rule wins. Done well items have no
   priority, so the P1 rule did not cover them.
3. `[C]` meant "the most likely P1" in the core and both lenses, and
   "the most likely P1 or P2" in both catalogs.
4. The lens Checks did not test the Done well rule. Only the core Check
   tested it, after the merge.
5. The `ml-critique-merge` Check did not test the Context section.

## Decision

The user decided each item:
1. **Credit before criticism.** The docs timeline now puts credit right
   after the top 3.
2. **Never cut a P1.** In `ml-critique-share-out` step 2, each P1 stays
   in the plan. A required topic gets a point only if the P1 points leave
   time. If not, the skill tells the user which topic has no point. Done
   well items are selected in the Done well order. Check questions 2 and
   4 and "Done when" changed to match.
3. **`[C]` = classic mistake, the most likely P1 or P2.** The catalog
   definition wins. The core and both lenses now use it.
4. **Lens Check question 6:** each strength says what breaks if it is
   lost, with no basic hygiene and at most 5. Each lens now has 6
   questions.
5. **Merge Check question 6:** each context conflict is in the Context
   section, with what was done. The merge now has 6 questions.

## Consequences

- A share-out with a short limit can leave a required topic with no
  point. The user sees this and decides in Discuss.
- The lens subagents catch a Done well filler before the merge, so the
  core merge has less to remove.
- Eval specs T9-T12 do not test the new questions. They are not run yet
  (evals on hold for token cost).
