# Fork into ml-modeling after high-level design; deep-dive and ml-modeling are alternatives

ADR 0001 made `design/deep-dive.md` the required upstream input for every
`ml-modeling-*` step. The first full run of the design path on a real,
log-shaped dataset (`labs/ml-riot-churn-2`, 2026-09-20) showed that gate is
the wrong one, and we moved the fork one step earlier: `ml-modeling-*` now
requires `prd/<topic>.md` + a fork-grade `design/high-level.md`, and does not
read `design/deep-dive.md` at all.

```
prd -> high-level -> [ deep-dive (paper) | ml-modeling data->features->train->evaluate ] -> delivery -> post-delivery
```

After high-level you pick one. The deep dive on paper and the hands-on chain
answer the same four questions (data, features, models, training); one writes
`design/deep-dive.md`, the other writes `modeling/01`-`04`. Delivery cites
whichever exists.

## Why

Three things happened in one session:

1. Writing an honest deep-dive required ad-hoc data profiling (null rates,
   class balance at each cutoff) - `ml-modeling-data`'s job, done inside a
   design skill. Without it the Data and Training sections would have been
   guesses, which is the "assumptions made up mid-chain" the gate was meant
   to prevent. The gate moved the guessing earlier; it did not remove it.
2. The decisive design change (revival horizon 28 -> 14 days, which halved
   the positive rate) came from `design/high-level.md`, not deep-dive, and
   forced a deep-dive rewrite. The decisions that steer modeling live in the
   PRD (metrics, scope) and the ML framing (target, label, horizon,
   population).
3. Monkey-mode built a correct, properly-labeled baseline (PR-AUC 0.477)
   with no deep-dive. Its grounding was three answers equivalent to PRD +
   framing. That is an existence proof that framing-level grounding is
   enough to start executing.

The deep-dive's four sections are a paper prediction of the four modeling
outputs, and the hash-and-ask drift machinery from 0001 existed largely to
police that duplication.

## Decision

- **Gate**: `prd/<topic>.md` + `design/high-level.md`. Both have POC modes,
  so the one-hour path is PRD (POC) -> high-level (POC) -> modeling.
- **Fork-grade framing** (`ml-system-design-high-level`): per model, the
  framing names prediction target, label definition and horizon, scoring
  population and cadence, unit of prediction, and known exclusions;
  Architecture's offline diagram names concrete source tables; "This folder
  builds: <model>" when several are framed. One model per project folder.
- **Grounding per step** (in the `ml-modeling` router): data <- framing +
  sources, decides the split and cutoffs itself and records them in
  `01-data.json`'s `dataset` block; features <- framing + `01-data`; train
  and multiagent <- Phasing's model class per phase + the algorithm matrix,
  decide loss and class weighting from `01-data`; evaluate <- PRD
  Metrics-offline + `dataset.split`.
- **Spec and drift**: `spec/<topic>.md` opens with `prd-hash:` and
  `high-level-hash:`. The detect-then-ask check from 0001 runs on both.
  Corrections to framing, sources, or phasing are offered back to
  `design/high-level.md` (hash refreshed); step-level decisions are recorded
  in the step's own `.md`, which is the hands-on deep dive's record.
- **Deep-dive skill**: unchanged in content, no longer upstream of anything.
  Its pre-draft checkpoint stays.

## Considered options

- **Keep the deep-dive gate** (0001 as written). Rejected: duplicates
  execution on paper, and the honest version already profiles data.
- **Make deep-dive data-informed** - let the design skill run profiling.
  Rejected: blurs the design and execution families into each other, which
  0001 deliberately kept separate.
- **Fork after high-level, deep-dive optional and read as hypotheses.**
  Rejected as the first draft of this ADR: adds a third state (both files
  present, which one wins?) and a back-fill step, for little gain over a
  clean either/or.
- **Fork after high-level, deep-dive and ml-modeling as alternatives.**
  Chosen.

## Consequences

- `ml-system-design-deep-dive` is no longer a dependency for any skill.
- `ml-system-design-high-level`'s framing carries the load; the skill's
  Done-when now enforces the fork-grade fields.
- Training-setup decisions that had no execution-side home (cutoffs, split,
  class weighting) now have one: `ml-modeling-data` and `ml-modeling-train`.
- Projects with only a `design/deep-dive.md` (e.g.
  `labs/ml-churn-prediction-1`) cannot run `ml-modeling-*` without a PRD and
  high-level; they were monkey-mode verification runs and will be re-run.
- Supersedes 0001's Path A / Path B tables and its first Consequence. The
  rest of 0001 (family split, spec shape, sequential vs parallel training)
  stands.
