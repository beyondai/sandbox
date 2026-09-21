---
name: ml-system-design-monkey-mlp
description: >-
  One-shot, fully autonomous embedding-MLP baseline builder — ask up to 3
  quick questions, then build and evaluate a fast (10-15 min) PyTorch
  embedding-MLP baseline in the background while you keep working. Never
  blocks — proceeds with self-inferred assumptions if you don't answer. A
  sibling to ml-system-design-monkey-mode: same fast/autonomous contract, but
  learned categorical embeddings instead of one-hot + a tree/linear model —
  reach for it when the task has high-cardinality identity columns (user/item
  ids, recommendation-shaped problems). Run by hand only, e.g.
  /ml-system-design-monkey-mlp song repeat-listen prediction.
disable-model-invocation: true
---

# Monkey MLP

A sibling to `ml-system-design-monkey-mode` — same independent, background,
never-blocks contract — but swaps the fast default model for a small PyTorch
embedding-MLP: every categorical column, especially high-cardinality identity
columns (a user id, an item/song id), gets a learned embedding instead of a
one-hot column, concatenated with standardized numerics, through a small MLP
head. Shares only the project-folder root with `monkey-mode`,
`ml-system-design-*`, and `ml-modeling-*` — writes only `monkey-mlp/`, reads
nothing under `design/`, `prd/`, or `modeling/`, and can run standalone or
alongside `monkey-mode` in the same project folder (disjoint folders, so no
write conflict — see `../README.md`'s "Running things concurrently") for a
direct tree-model-vs-embedding-model comparison.

## When to reach for this instead of (or alongside) monkey-mode

Prefer monkey-mode's tree/linear default in general — it needs no early
stopping, no architecture choice, and is one `.fit()` call. Reach for
monkey-MLP specifically when the task has **high-cardinality identity
columns** (user ids, item/song ids, anything with thousands+ unique values)
where an embedding can absorb identity-level signal a one-hot + tree model
can't cheaply represent — recommendation, repeat-purchase/repeat-listen
prediction, anything collaborative-filtering-shaped.

On a real run (KKBOX repeat-listen prediction, 480K train / 120K test rows),
a model built exactly this way landed within ~0.01 AUC of a properly
feature-engineered Random Forest (0.7271 vs. 0.7361) with zero hand-built
features — the embeddings implicitly captured what hand-built
`msno_repeat_rate` / `song_repeat_rate` aggregate columns captured
explicitly. Treat that gap as a reasonable expectation, not a guarantee:
"get close to a tuned model for free," not "beat it."

## Process

1. Resolve the project folder — same as `ml-system-design-monkey-mode`: check
   for `ml-<topic-slug>-*`, use `-1` if none exist, ask which to use if some
   do.
2. Fire the same 3 questions as `ml-system-design-monkey-mode` via
   AskUserQuestion (task + data, primary metric, success bar) — same
   fallback philosophy, never block. See that skill's "The 3 questions"
   section for the exact text and fallbacks; not duplicated here so the two
   files can't drift out of sync silently.
3. Dispatch a background `general-purpose` agent with everything it needs to
   run unattended: the resolved task/data/metric/success-bar (each marked
   answered-by-user or self-inferred), the fast defaults and the two
   non-negotiable eval rules below, the deliverable list, the output path.

   Same shared-folder etiquette as monkey-mode: the project folder may be
   populated concurrently by other in-progress work and must be treated as
   shared, not owned — never delete or reset the project-folder root or any
   sibling directory (`prd/`, `design/`, `adr/`, `spec/`, `modeling/`,
   `monkey-mode/`), only ever create `monkey-mlp/` additively with
   `mkdir -p` and write inside it.

   Instruct the agent to verify `pandas`/`numpy`/`scikit-learn`/`torch`
   import via `uv run python3 -c "import pandas, numpy, sklearn, torch"` run
   from inside the project folder — this resolves the sandbox root's shared
   `pyproject.toml`/`.venv` (confirmed already stocked with `torch==2.2.2`,
   MPS available, on this machine), not the bare ambient `python3`. Only if
   that genuinely fails, run `uv add torch` from the sandbox root (never a
   project-local `.venv` — same reasoning as monkey-mode). Device selection:
   `torch.backends.mps.is_available()` -> `"mps"`, else
   `torch.cuda.is_available()` -> `"cuda"`, else `"cpu"`.
4. When it reports back, surface the results.

## Fast defaults — build with these, don't ask

- **Cleaning**: same as monkey-mode — drop or median-impute nulls, nothing
  fancier.
- **Features**: every categorical column gets a learned `nn.Embedding`
  (`min(50, cardinality // 2 + 1)` dims — the cap keeps identity-column
  embeddings from ballooning memory on huge vocabularies), concatenated with
  standard-scaled numerics. No target encoding, no interaction features, no
  aggregate/leave-one-out features — the embeddings are the feature
  engineering here.
- **Model**: one fixed architecture, not a search —
  `embeddings -> concat -> Linear(256) -> ReLU -> Dropout(0.1) -> Linear(64)
  -> ReLU -> Linear(1)`, `BCEWithLogitsLoss`, Adam `lr=2e-3`. Batch size 2048
  under ~1M rows, 8192 above. Not a comparison — one architecture, trained
  once (per the rules below).
- **Eval — the two rules that are NOT optional, unlike everything else in
  this list**:
  1. Carve an internal validation split **out of the train rows only** (15%,
     fixed seed) before touching the model at all. Fit categorical
     vocabularies on the remaining fit-split only; unseen categories in
     validation or test map to an explicit "unknown" code (`0`), never a
     silently-included category. Train with early stopping on that internal
     validation AUC (patience 3, max 25 epochs), and load only the
     best-by-internal-validation epoch's weights afterward.
  2. Score the held-out test set **exactly once**, after the model is
     already fixed by step 1. Never pick an epoch, a checkpoint, or any
     other choice by watching test-set AUC during training. This is the one
     place a from-scratch network differs from monkey-mode's single-fit
     tree model: a tree fit once has no epoch loop to leak through, but a
     network's training loop does, and skipping this invisibly inflates the
     reported number. Verified concretely on a real run: an MLP whose
     stopping epoch was chosen by watching test AUC directly reported
     0.7309; the identical architecture, retrained with the stopping point
     chosen from internal validation only, scored a true 0.7271 — a leak of
     about 0.004 AUC that would have gone unnoticed without this discipline.
  3. If a sample was taken because the source table is large, state its
     size **as an explicit, bolded percentage of the full source** in
     `report.md`'s Requirements/Input sections — same rule and same reason
     as monkey-mode's Eval bullet.

## Deliverable

Write `<project-folder>/monkey-mlp/report.md` (format: same seven sections as
`ml-system-design-monkey-mode`'s Deliverable — Requirements, Input, Design,
Implementation, Results, Learnings, Suggested Next Steps), with one addition
to Results: state the internal-validation epoch selected and its AUC,
separately from the final test AUC, and say explicitly that the test set was
scored exactly once. If `monkey-mode/report.md` already exists in this
project folder, add a one-line comparison against its reported metric in
Learnings — say plainly whether it's a same-test-set comparison or only an
approximate one (different sample, different split), since that distinction
is easy to blur and matters for judging the result.

Mark, per item in Requirements, whether it came from the user's answer or
self-inference — same rule as monkey-mode.

Done when `report.md` exists with all seven sections populated by a real run
(real code, real numbers, a final test AUC computed exactly once) — not
placeholders.

If this run turns up a bug or a better design in this skill, or you ask for a
change to how it works, log it — see `../ml-system-design/SKILL.md`'s Skill
improvement log.
