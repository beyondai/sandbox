# Critique: full coverage, importance order, Quick mode, context, view

## Context

On 2026-10-09 the user prepared a Riot interview: critique a junior
engineer's report on a wiki article recommender
(`labs/ml-riot-wiki-recommender-1/interview/`). A comparison of the
critique skills with the design and modeling skills found gaps:
- 10 skill items had no catalog check (definition Team, baseline parts,
  feature list, test plan and CI/CD, execution, Democratize, data
  profile, proxy data, ranking evaluation, serving mode and cost).
- The order rules had no single sort key.
- Brief mode limited the checks and the presentation to 45 minutes. The
  user wants a limit on the whole run.
- The skill had no place for the purpose of a critique (an interview
  brief), and it assumed a fresh view by default.
- One mixed report had no lens rule, and the Recommendation playbook had
  no item-to-item variant.

## Decision

1. **Full coverage in Normal mode.** `ml-critique/references/coverage.md`
   maps each design and modeling skill item to catalog IDs. New items:
   system C7, G0, G1a, I10, I11, J6; modeling B8, B9, I11, K5. Modeling
   I8 becomes `[C]`.
2. **One sort key:** priority, then upstream, then effect, then
   confidence. Check order: playbook classic mistakes, then sections in
   order, `[C]` items first inside a section.
3. **Quick replaces Brief.** The whole run takes 2 hours at most. Checks
   follow the importance order until the budget is used. New sections:
   Appendix (found, not presented) and Not checked (skipped for time).
4. **Critique context.** Select asks for it each run. General rules
   apply; the context wins only on a conflict, and each conflict is
   noted in chat and in a Context section. The lenses get the context.
5. **View asked each run:** Fresh or With my design. No default.
6. **Router:** one file is routed by its sections; mixed content gets
   both lenses.
7. **Playbook:** Recommendation gets an item-to-item variant.

## Consequences

- Critique files gain a Context section (both modes), and Quick files
  gain Appendix and Not checked. Older critique files have the old
  sections.
- "Brief" is no longer a mode name; the keyword still selects Quick.
- Each new design or modeling skill item needs a coverage row, or it has
  no critique check.
- Select always waits for the view and context answers, so a run starts
  one message later.
- New evals T5-T8 in `ml-critique/tests/2026-10-09-skill-test.md` test
  these changes. They are written, not run.
