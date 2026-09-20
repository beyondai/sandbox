---
name: ml-system-design-monkey-mode
description: One-shot, fully autonomous ML baseline builder — ask up to 3 quick questions, then build and evaluate a fast (5-10 min) baseline in the background while you keep working. Never blocks — proceeds with self-inferred assumptions if you don't answer. A third, independent track alongside the whole-design path and the ml-modeling-* path. Run by hand only, e.g. /ml-system-design-monkey-mode churn prediction for a subscription app.
disable-model-invocation: true
---

# Monkey Mode

A third, independent track alongside `ml-system-design-*` (the whole design doc) and `ml-modeling-*` (the deliberate data→features→train→evaluate chain) — shares only the project-folder root with both, nothing else. Doesn't read `design/deep-dive.md`, doesn't write into `modeling/`, doesn't require either path to have run first. The point: one line in, a runnable baseline out, in the background, while you keep working on the real design.

## Process

1. Resolve the project folder: same numbering as `ml-system-design-prd` — check for `ml-<topic-slug>-*`, use `-1` if none exist, ask which to use if some do.
2. Fire the 3 questions below via AskUserQuestion, each with a recommended default. **Never block**: whether answered, partially answered, or skipped, proceed immediately — an unanswered item falls back to its self-inferred default, not a re-ask.
3. Dispatch a background `general-purpose` agent (no worktree needed — same reasoning as `ml-modeling-multiagent`: this is one self-contained script, not concurrent edits) with everything it needs to run unattended: the resolved task/data/metric/success-bar (each marked answered-by-user or self-inferred), the fast defaults below, the deliverable list, and the output path. Tell the user it's running in the background and they can keep working on the regular flow.
4. When it reports back, surface the results.

## The 3 questions — never blocking

1. **Task + data**: what's being predicted, and where's the data?
   Self-inferred fallback: read the task type (classification/regression/ranking) straight out of the prompt's own wording. If no data is referenced, generate a small, reasonable synthetic dataset shaped like the described problem.
2. **Primary metric**: what should the baseline be scored on?
   Self-inferred fallback: the standard metric for the inferred task — F1 for imbalanced-looking binary classification, RMSE for regression, nDCG for ranking.
3. **Success bar**: what counts as "good enough" for a first baseline?
   Self-inferred fallback: an actual assumed target number based on the problem and data in hand (e.g. "F1 ~0.65-0.75 for a roughly balanced synthetic binary classification") — not just "beat random." Runnable is the floor: something that actually executes and reports a real number always outranks a good number.

Everything else (cleaning, transforms, model pick, eval split, sample size) is a stated assumption, never a 4th question — in both the answered and self-inferred paths.

## Fast defaults — build with these, don't ask

- **Cleaning**: drop or median-impute nulls, nothing fancier.
- **Features**: standard-scale numerics, one-hot low-cardinality categoricals. No embeddings, no elaborate engineering.
- **Model**: one fast, decent pick — see `ml-modeling-train`'s algorithm-selection matrix, "start simple" row (logistic/linear regression, or a single small tree ensemble for tabular data). Not a comparison — one model, trained once.
- **Eval**: a held-out split (or a small sampled subset if the dataset is large), scored on the resolved primary metric.

## Deliverable

Write `<project-folder>/monkey-mode/report.md` with exactly these sections:

- **Requirements** — the simple/assumed version, from the 3 answers or their inferred fallbacks
- **Input** — data source (real path, or synthetic-generation description + seed)
- **Design** — the approach taken and why (the fast defaults above, applied to this problem)
- **Implementation** — the actual code that ran, not a template
- **Results** — real metrics from the eval step, against the stated success bar
- **Learnings** — what the baseline reveals (is the target learnable, any data issue found, anything surprising)
- **Suggested Next Steps** — what this implies for the regular flow, either path (e.g. "this suggests the model choice in `design/deep-dive.md` is a reasonable bet") — without monkey-mode itself ever reading from or writing into `design/`, `modeling/`, `prd/`, `adr/`, or `spec/`

Mark, per item in Requirements, whether it came from the user's answer or self-inference — the one place this doc must not blur "you told me" with "I assumed."

Done when `report.md` exists with all six sections populated by a real run (real code, real numbers) — not placeholders.

If this run turns up a bug or a better design in this skill, or you ask for a change to how it works, log it — see `../ml-system-design/SKILL.md`'s Skill improvement log.
