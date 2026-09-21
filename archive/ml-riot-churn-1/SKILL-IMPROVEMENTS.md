## 2026-09-20 — ml-system-design-deep-dive
- **Source**: user-requested
- **Status**: adopted (2026-09-20)
- **Finding**: On the first turn of a Regular-mode run, the skill went straight from the request to a fully-written `design/deep-dive.md` (Data, Features, Models, Training all filled in, with real numbers pulled from the data) without first confirming the problem definition or checking data availability with the user. The skill's own Draft/Regular instruction ("answer each item... ask if unknown, never invent") is about not inventing values within a section, but there's no checkpoint before the write that surfaces the problem framing and a go/no-go on data existing at all — both of which are cheap to confirm and expensive to redo work over if wrong.
- **Suggested change**: Before drafting the four sections in Regular mode, state the problem definition back to the user in 1-3 sentences and confirm the required data sources actually exist (file listing / row counts, not a full profile) as an explicit checkpoint. Only proceed to write the full Data/Features/Models/Training sections after that checkpoint is acknowledged, rather than folding it into the same turn as the full write-up.

Applied to `.agents/skills/personal/ml-system-design-deep-dive/SKILL.md` as a new "Before drafting (Regular mode)" section.

## 2026-09-20 — ml-system-design
- **Source**: user-requested
- **Status**: adopted (2026-09-20)
- **Finding**: Kicking off a new project from a bare request ("let's practice X with regular ml design") went straight to `ml-system-design-deep-dive` instead of first asking whether to (a) launch `ml-system-design-monkey-mode` in parallel as an independent fast baseline, and (b) start with `ml-system-design-prd`/`ml-system-design-definition` to scope the project before drafting into deep-dive. Both are currently documented as "run by hand" / optional, so nothing in the flow prompts the user to consider them before drafting begins — the user has to already know to ask for them.
- **Suggested change**: At the start of any new project (no explicit section named by the user), ask two things up front before invoking any drafting skill: (1) whether to launch `ml-system-design-monkey-mode` in parallel as a background baseline, and (2) confirm starting from `ml-system-design-prd`/`ml-system-design-definition` rather than jumping straight to a later section like deep-dive.

Applied to `.agents/skills/personal/ml-system-design/SKILL.md` (the "Starting a new project" paragraph) and `docs/ML-SKILLS-GUIDE.md` (design-path diagram).

## 2026-09-20 — ml-system-design-monkey-mode
- **Source**: user-requested
- **Status**: adopted (2026-09-20)
- **Finding**: Question 3 ("success bar") offers "a specific number" as an option, but when the user doesn't already have one in hand (no prior baseline for this problem/domain exists), the skill has no path for grounding that number other than the self-inferred guess-from-the-problem-shape fallback. The user wanted to do a quick real-world lookup (industry-typical player churn rates) first, then set the target from that, rather than either picking an arbitrary number or falling back to a pure guess.
- **Suggested change**: When the user opts to set a specific success-bar number but signals they don't have one yet, offer a quick research step (a web search for a domain-typical benchmark, e.g. "typical game player churn rate" or "typical PR-AUC for churn models") as a third path alongside "self-inferred guess" and "user already knows the number" — cite the source and use it to ground the target instead of guessing blind.

Applied to `.agents/skills/personal/ml-system-design-monkey-mode/SKILL.md` (question 3 now offers a "look one up" path with a population-mismatch caution).
