# Principle 2 skill-check fixes, Principle 3, and the markdown template

## Context

On 2026-10-09 the user asked for the skill checks on the `ml-*` design
and critique skills. Both scripts printed `OK`. The manual checklists
found 4 problems. All of them came from ADR 0022:
1. `ml-system-design-prd` step 3 had its own copy of the Definition
   branches. The copy had no "Metrics, intended behavior" branch. So the
   PRD interview did not ask for it, and `prd/` did not have it. The
   skill also says "keep no copy here".
2. `ml-critique` rule 4 named only Principle 1. The critique guide says
   the review also applies Principle 2.
3. "Related" in `ml-system-design` and `ml-modeling` named only
   Principle 1.
4. The `ml-system-design-definition` description did not name the
   intended behavior, so a request about a gamed metric may not trigger
   it.

## Decision

The user said "fix" for all 4:
1. **The PRD reads the checklist each run.** Step 3 makes one branch for
   each bullet of the `ml-system-design-definition` checklist, with no
   list in the PRD skill. PRD Check question 3 also asks for the ways to
   game the primary metric, each with a guardrail.
2. **The critique core names Principle 2** (system B7, modeling I12).
3. **Both routers name Principle 2** in their pointer to
   `ml-design-principles.md`.
4. **The definition description** adds "intended behavior" and "ways a
   model can game its metric".

### Part 2: the docs and the principles follow ADR 0022

The user then asked to bring the docs, the README, the principles, and
the design template up to date with the production rules of ADR 0022.
ADR 0022 put 3 of its 4 lessons only in catalog items and skill bullets:
- full phase gates, and a proven version kept shippable;
- a staged rollout with an internal stage;
- a retrain that fits the change cadence.

The principles file had no principle for them. The delivery skill had no
retraining item, but the coverage map pointed F7 at delivery. The
template was plain text. It did not have these items that the skills
ask for: the event to predict, the floor, the build decision, the
framing details, the fallback trigger, and the output review.

Decision:
- **Principle 3 in `ml-design-principles.md`:** a proven version ships,
  and it keeps up with change. It collects the ADR 0022 rules, with no
  new rule. A summary table at the top lists the 3 principles.
- **Pointers to Principle 3** in high-level, deep-dive, delivery, the
  critique core, both lenses, and the router.
- **Delivery has a Retraining item:** the triggers (drift and each
  scheduled change), the owner after launch, and the runbook. Check
  question 6 tests it. The description names it.
- **The template is `docs/ml-design-template.md`:** light markdown
  (`#` headings, lists, one code block), so it reads well in a terminal
  and in a markdown reader. It has each item of the design skills, with
  the principle next to the items that apply it.
- **Docs:** a "Design principles" section in `docs/ML-SKILLS-GUIDE.md`
  and in the skills README; Principle 3 findings in
  `docs/ML-CRITIQUE-GUIDE.md`.

## Consequences

- A new Definition bullet reaches the PRD interview with no PRD edit.
- A delivery section has one more required item (Retraining), so older
  design docs fail delivery Check question 6.
- The template path changed from `.txt` to `.md`.
- PRDs written before this change have no intended behavior. A
  `-definition` Review or a critique (B7) finds the gap.
- Eval specs do not test the PRD seed. They are not run yet (evals on
  hold for token cost).
