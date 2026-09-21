---
name: ml-system-design-monkey-mode
description: >-
  One-shot, fully autonomous ML baseline builder — ask up to 3 quick questions,
  then build and evaluate a fast (5-10 min) baseline in the background while you
  keep working. Never blocks — proceeds with self-inferred assumptions if you
  don't answer. A third, independent track alongside the whole-design path and
  the ml-modeling-* path. Run by hand only, e.g. /ml-system-design-monkey-mode
  churn prediction for a subscription app.
disable-model-invocation: true
---

# Monkey Mode

A third, independent track alongside `ml-system-design-*` (the whole design doc)
and `ml-modeling-*` (the deliberate data→features→train→evaluate chain) — shares
only the project-folder root with both, nothing else. Doesn't read
`design/` or `prd/`, doesn't write into `modeling/`, doesn't require either
path to have run first. The point: one line in, a runnable baseline out, in the
background, while you keep working on the real design.

For tasks with high-cardinality identity columns (user/item ids,
recommendation-shaped problems), see the sibling
`ml-system-design-monkey-mlp` — same contract, an embedding-MLP instead of
this skill's tree/linear default, writes to a disjoint `monkey-mlp/` folder
so both can run on the same project.

## Process

1. Resolve the project folder: same numbering as `ml-system-design-prd` — check
   for `ml-<topic-slug>-*`, use `-1` if none exist, ask which to use if some do.
2. Fire the 3 questions below via AskUserQuestion, each with a recommended
   default. **Never block**: whether answered, partially answered, or skipped,
   proceed immediately — an unanswered item falls back to its self-inferred
   default, not a re-ask.
3. Dispatch a background `general-purpose` agent (no worktree needed — same
   reasoning as `ml-modeling-multiagent`: this is one self-contained script, not
   concurrent edits) with everything it needs to run unattended: the resolved
   task/data/metric/success-bar (each marked answered-by-user or self-inferred),
   the fast defaults below, the deliverable list, and the output path. Tell the
   user it's running in the background and they can keep working on the regular
   flow.

   The project folder may be populated concurrently by other in-progress work
   (PRD/design running in the foreground session) and must be treated as
   shared, not owned: instruct the agent to never delete or reset the
   project-folder root or any sibling directory (`prd/`, `design/`, `adr/`,
   `spec/`, `modeling/`) — only ever create `monkey-mode/` additively with
   `mkdir -p` and write inside it. A prompt phrase like "the project folder
   does not exist yet" describes the folder's state before this run, not
   permission to reset it if it appears mid-run.

   Instruct the agent to verify `pandas`/`scikit-learn`/`numpy` import via
   `uv run python3 -c "import pandas, numpy, sklearn"` run from inside the
   project folder — this resolves the sandbox root's shared `pyproject.toml`/
   `.venv` (confirmed already stocked with pandas, numpy, scikit-learn,
   matplotlib, plotly, streamlit, and more), not the bare ambient `python3`.
   Only if that genuinely fails (a package truly isn't in the shared env) run
   `uv add <pkg>` from the sandbox root (not the project folder) so the fix
   lands in the shared `pyproject.toml`/`uv.lock` and benefits every future
   project — never bootstrap a project-local `.venv` as the first move; that
   duplicates work and silently diverges from the shared environment. Note
   any such addition in the report's Learnings.
4. When it reports back, surface the results.

## The 3 questions — never blocking

1. **Task + data**: what's being predicted, and where's the data?
   Self-inferred fallback: read the task type
   (classification/regression/ranking) straight out of the prompt's own wording.
   If no data is referenced, generate a small, reasonable synthetic dataset
   shaped like the described problem.
2. **Primary metric**: what should the baseline be scored on?
   Self-inferred fallback: the standard metric for the inferred task — F1 for
   imbalanced-looking binary classification, RMSE for regression, nDCG for
   ranking.
3. **Success bar**: what counts as "good enough" for a first baseline? Offer
   three ways to answer: a number the user already has; "look one up" — a
   quick web search for a domain benchmark (typical model performance for
   this kind of task, cited), translated into the chosen metric and stated as
   a soft target; or leave it to the fallback. Time-box the "look one up"
   search to 2 minutes — take the best citation found in that window rather
   than continuing to search for a perfect match. Watch for benchmarks that
   measure a different population than the task (e.g. new-install churn vs.
   retained-player lapse) and say so rather than adopting the number.
   Self-inferred fallback: an actual assumed target number based on the problem
   and data in hand (e.g. "F1 ~0.65-0.75 for a roughly balanced synthetic binary
   classification") — not just "beat random." Runnable is the floor: something
   that actually executes and reports a real number always outranks a good
   number.

Everything else (cleaning, transforms, model pick, eval split, sample size) is a
stated assumption, never a 4th question — in both the answered and self-inferred
paths.

## Fast defaults — build with these, don't ask

- **Cleaning**: drop or median-impute nulls, nothing fancier.
- **Features**: standard-scale numerics, one-hot low-cardinality categoricals.
  No embeddings, no elaborate engineering.
- **Model**: one fast, decent pick — see `ml-modeling-train`'s
  algorithm-selection matrix, "start simple" row (logistic/linear regression, or
  a single small tree ensemble for tabular data). Not a comparison — one model,
  trained once.
- **Eval**: a held-out split (or a small sampled subset if the dataset is
  large), scored on the resolved primary metric. If a sample was taken,
  state its size **as an explicit, bolded percentage of the full source**
  in `report.md`'s Requirements/Input sections - not just the raw row
  count buried in a Suggested Next Steps aside (e.g. "**a 600,000-row
  sample, ~8.1% of the full 7,377,419-row `train.csv`**"). This has gone
  unnoticed before when only the raw count was given up front, and it
  matters for judging results later.

## Deliverable

Write `<project-folder>/monkey-mode/report.md` (format:
`../ml-system-design/SKILL.md`, "Output docs") with exactly these sections:

- **Requirements** — the simple/assumed version, from the 3 answers or their
  inferred fallbacks
- **Input** — data source (real path, or synthetic-generation description +
  seed)
- **Design** — the approach taken and why (the fast defaults above, applied to
  this problem)
- **Implementation** — the actual code that ran, not a template
- **Results** — real metrics from the eval step, against the stated success bar
- **Learnings** — what the baseline reveals (is the target learnable, any data
  issue found, anything surprising)
- **Suggested Next Steps** — what this implies for the regular flow, either path
  (e.g. "this suggests the V1 model class in `design/high-level.md`'s Phasing
  is a reasonable bet") — without monkey-mode itself ever reading from or writing into
  `design/`, `modeling/`, `prd/`, `adr/`, or `spec/`

Mark, per item in Requirements, whether it came from the user's answer or
self-inference — the one place this doc must not blur "you told me" with "I
assumed."

Done when `report.md` exists with all six sections populated by a real run (real
code, real numbers) — not placeholders.

If this run turns up a bug or a better design in this skill, or you ask for a
change to how it works, log it — see `../ml-system-design/SKILL.md`'s Skill
improvement log.
