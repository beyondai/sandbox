# Data cleaning is a phase inside ml-modeling-data, not a new step

`ml-modeling-data`'s Profile section only ever *flagged* data-quality issues
(nulls, duplicates, obvious outliers) into `quality_flags` - nothing in the
`ml-modeling-*` family or its ADRs instructed fixing them. This surfaced
concretely on the KKBOX practice project: `bd` (member age) had implausible
values (<=0 or >100) for 40% of rows, masked to null by hand mid-session, on
direct user request, with no skill instruction behind it. The gap was real,
not hypothetical, so cleaning now gets an explicit `## Clean` section inside
`ml-modeling-data`, right after Profile - same output files
(`01-data.md`/`.json`), no renumbering of the chain.

## Considered options

- **New standalone skill** (e.g. `ml-modeling-clean` as its own numbered
  step, `01-data -> 02-clean -> 03-features -> ...`): more discoverable and
  composable as an independent invocation, and cleanly separates "observe"
  from "act." Rejected: renumbers every downstream artifact
  (`02-features.md` -> `03-`, `03-train.md` -> `04-`, `04-evaluate.md` ->
  `05-`), the router's step table, the shared dashboard template's
  hardcoded `01-data.json`/`04-evaluate.json` paths, and creates a
  numbering mismatch against every project already using the old scheme
  (e.g. `labs/ml-riot-churn-1`). Too large a migration for what is
  fundamentally one more phase of an existing step, not a new concern that
  needs its own file-based handoff.
- **Extend `ml-modeling-data`** (chosen): same output files, no
  renumbering, no cascading edits anywhere else in the family. Matches what
  already happened by hand in the KKBOX project - a "Clean" phase after
  Profile is exactly the order that occurred there in practice (profile
  surfaced the flag, cleaning acted on it, the profile was then re-run).

## Decision

Data cleaning lives inside `ml-modeling-data`, as a `## Clean` section
between `## Profile` and `## Dashboard`. The distinguishing test for what
gets cleaned vs. left alone: **would a domain expert call this impossible,
or just unusual?** Impossible values (negative age, a missingness sentinel,
exact duplicate rows) get fixed and the profile re-run; unusual-but-real
values (a long song, a large purchase) stay exactly as `quality_flags`
already handles them - surfaced, not touched.

## Consequences

- `ml-modeling-data`'s scope grows from build/register + profile to
  build/register + profile + clean, still producing one file pair
  (`01-data.md`/`.json`) as output - no schema change to `01-data.json`,
  since `quality_flags`/`numeric_distributions`/`nulls` already carry
  cleaned values fine, only their content changes.
- The router's step-1 one-liner and its "Where each step gets its
  grounding" table both now name cleaning as something this step decides
  and records (`ml-modeling/SKILL.md`).
- `ml-modeling-features` and every later step can assume the labeled table
  they read has already had genuine errors fixed - they don't need to
  re-derive that judgment call themselves.
