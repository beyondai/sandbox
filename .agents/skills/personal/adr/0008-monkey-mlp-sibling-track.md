# Monkey-MLP is a sibling skill, not a model option on monkey-mode

On the KKBOX repeat-listen project (`labs/ml-kkbox-recommendation-1`),
monkey-mode's tree baseline scored AUC 0.6727 on 12 raw columns. A
from-scratch PyTorch embedding-MLP, built by hand in the same session with
zero feature engineering, reached 0.7271 on the project's own held-out test
split - within ~0.01 of the fully feature-engineered Random Forest (0.7361) -
because `msno`/`song_id` are exactly the high-cardinality identity columns
embeddings are suited for. Getting that honest 0.7271 took a second attempt:
the first version picked its stopping epoch by watching test-set AUC during
training and reported an inflated 0.7309. monkey-mode's "one fast, decent
pick... trained once" contract has no mechanism for this failure mode, because
a tree model fit once has no epoch loop to leak through. Adding a neural-net
option to monkey-mode would quietly import a risk its own design is built to
avoid.

## Considered options

- **Add `model: mlp` as an option in `ml-system-design-monkey-mode`'s Fast
  defaults**, gated by a 4th question or an inferred condition. Rejected:
  monkey-mode's value is "no tuning, no babysitting, one model, trained
  once, three questions, never a fourth." A neural net always needs an
  early-stopping decision a tree model doesn't - either that becomes a
  silent, model-specific exception to monkey-mode's own simplicity rule, or
  it gets skipped and the tree-model default quietly inherits a training
  loop's leak risk nobody asked for.
- **Fold this into `ml-modeling-train`'s algorithm-selection matrix instead**
  - it already has a "Large data, complex patterns -> Neural network" row.
  Rejected: that row belongs to the deliberate, reviewed `ml-modeling-*`
  chain (CV, experiment logging, a human checkpoint after each step), not a
  background, autonomous, never-blocks baseline. The two families are
  intentionally split by rigor level (0001); collapsing them for one
  algorithm choice blurs a line drawn on purpose.
- **New sibling skill, same contract as monkey-mode, separate output
  folder.** Chosen.

## Decision

- New skill `ml-system-design-monkey-mlp`: same three-question,
  never-blocks, background-dispatch contract as monkey-mode, same
  Requirements/Input/Design/Implementation/Results/Learnings/Suggested-Next-Steps
  report shape. Writes only `monkey-mlp/report.md` - disjoint from
  `monkey-mode/report.md`, so both can run on one project folder without a
  write conflict, same "isolation is the folder split" pattern as every
  other concurrent-write case in `README.md`.
- Two of its Eval defaults are marked non-negotiable, unlike the rest of its
  fast-defaults list: early stopping is chosen only from a validation split
  carved out of train rows, never from the test set; the test set is scored
  exactly once, after the model is already fixed. This is the one place
  monkey-mlp is deliberately less "monkey-simple" than monkey-mode - the
  specific risk a training-loop model carries that a single-fit tree model
  does not.
- Which to use is a documented judgment call, not a strict rule: monkey-mode
  stays the general-purpose default; monkey-mlp is for tasks with
  high-cardinality identity columns (user/item ids, recommendation-shaped
  problems) where an embedding is plausibly a better fit.

## Consequences

- A project folder can now carry two independent, disjoint-writing
  background baselines (`monkey-mode/` and `monkey-mlp/`) for a direct
  tree-vs-embedding comparison - `README.md`'s "Running things concurrently"
  table gains this as a third combination alongside "design path +
  monkey-mode" and "design continues while `ml-modeling-*` runs."
- `torch` joins the shared sandbox venv's expected-available packages
  alongside pandas/numpy/scikit-learn (confirmed present: 2.2.2, MPS
  enabled) - monkey-mlp's env check includes it, same "check the shared venv
  first, `uv add torch` at the sandbox root only if truly missing" rule
  monkey-mode already applies to its own three packages.
- `docs/ML-SKILLS-GUIDE.md` (shape diagram, command reference, parameters
  table) and `README.md`'s Monkey-mode section gain matching entries for the
  new skill, and `ml-system-design-monkey-mode/SKILL.md` gains a one-line
  pointer to the sibling, so it's discoverable from either side.
