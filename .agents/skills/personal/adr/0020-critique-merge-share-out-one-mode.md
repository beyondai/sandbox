# Critique: merge and share-out skills, one mode, user tags

## Context

On 2026-10-09 the user ran a second, independent critique of the Riot
interview report (`labs/ml-riot-wiki-recommender-1/critique/2026-10-09-both-v2.md`,
Normal mode, fresh). The first was a Quick run (`2026-10-09-both-v1.md`).
The session showed:
- **Time.** The agent part of each run took minutes, in both modes. The
  2-hour Quick budget came from the interview brief ("prepare in less
  than 2 hours"). That limit is the user's share-out time, not the
  critique's. The skill recommended Quick only because of that limit, in
  both runs, and the user chose Normal.
- **Merge.** 2 independent critiques of one report existed. No skill
  joined them into one final critique.
- **Share-out.** No skill turned a critique into what to discuss in a
  fixed time for an audience. The user asked for one, named "share-out"
  (not "presentation").
- **User findings.** The user added strengths and questions in Converge.
  The file mixed them with the lens findings. The user asked to separate
  their own new findings in all reports.
- **Done well.** The merged list had 10 strengths. The user agreed with 2
  and said the others "seem for encouragement". This rule comes from that
  user comment. A review of the user's 6 rejections found 5 fair and 1
  not (the click label was a real design choice), so the rule tests
  "costly to lose", not "few".
- **Text-only report.** Both lenses gave the same findings on the split,
  the metric, the loss, and the filters, and gave different priorities to
  2 of them (C4, C8). Normal mode asked for probe output that a text-only
  report cannot give. The deferred entry for this case met its unblock
  condition.

## Decision

1. **One critique mode.** Remove Quick mode, its keywords, budgets,
   Appendix, and Not checked. Each run checks the full catalog. Select
   asks 2 questions (view, context). A time limit in the critique context
   is not a conflict: it is recorded for the share-out.
2. **`ml-critique-merge`** (new skill). Input: 2 or more critiques of one
   write-up and an optional critique context. Steps: Select, Merge,
   Propose, Discuss (rounds until the user says to write), Write
   (`critique/<date>-final.md`), Check. Merge rules: join the same
   problem, keep the stronger evidence, make each priority, claim, or
   decision conflict a question, keep `[user]` and `[ref]` tags and each
   source decision, move rejected items to a Rejected section.
3. **`ml-critique-share-out`** (new skill). Input: 1 final critique (it
   runs `ml-critique-merge` first if given several) and a share-out
   context. It reads the share-out limit, the required topics, and the
   audience. Steps: Select, Propose, Discuss (until "write"), Write
   (`critique/<date>-share-out.md`), Check. A reference file gives the
   delivery rules by context type (working-session interview, team design
   review, launch review).
4. **`[user]` tag.** In Converge, each new item that the user adds gets
   `[user]`. All 3 critique skills keep the tag.
5. **Done well rule** (from the user's comment). List a strength only if
   losing it would make the result worse, with what breaks. No basic
   hygiene. At most 5.
6. **Text-only and mixed reports.** When both lenses run on one file, the
   core tells each lens the sections it owns. For a text-only write-up,
   evidence is a quote and a shown calculation.

## Consequences

- One path for every critique. A short share-out no longer makes the
  critique shallow; the share-out skill cuts for time.
- 3 files per share-out can exist in `critique/`: the critiques, the
  final critique, and the share-out. Each step keeps its inputs
  unchanged.
- Older test specs T5-T7 (`ml-critique/tests/2026-10-09-skill-test.md`)
  test Quick mode. They stay as history.
- The new skills have eval specs (T9-T12) that are not run yet (evals on
  hold for token cost).
- Log entries adopted: critique time estimates (modified: Quick removed),
  tag user findings, Done well filter, text-only hybrid report
  (reopened), share-out and merge skills.
