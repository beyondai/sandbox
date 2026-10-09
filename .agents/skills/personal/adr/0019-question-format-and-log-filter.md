# Critique questions explain their value; the log needs evidence

## Context

On 2026-10-09 the user ran a Quick, fresh critique of the Riot interview
report (`labs/ml-riot-wiki-recommender-1/critique/2026-10-09-both-v1.md`).
Two things came out of the session:
- The user did not see why the question "What share of positives are
  on-page link clicks?" mattered. The value became clear only after an
  explanation: what the question means, why it matters, and what each
  answer changes. The user called this part very good. The vague claim
  "recommendations are subjective" also needed a split into its 2
  meanings (label noise, personalization).
- The session logged 7 skill issues. 6 came from the lens subagents,
  which were asked to report issues. The user saw only 1 as an obvious
  improvement. A review found that the lenses had found the other
  problems anyway, through the playbook or the existing catalog.

## Decision

1. **Question format.** Each part-4 question gives the expected answer,
   why it matters, and what each likely answer changes. A vague claim in
   the write-up gets an "in which sense?" question, with each meaning and
   its fix. Applied in `ml-critique` (step 2) and both lenses (step 5 and
   Check).
2. **Log filter.** An agent-found entry needs evidence that the skill
   made the work worse: a missed, wrong, or late result, or extra work for
   the user. The lenses return a skill issue only under the same rule.
   Applied in `ml-system-design` ("Skill improvement log"), `ml-critique`
   (step 2.3), and both lens Checks.
3. **Access filter in more playbooks.** Search ranking and RAG get one
   classic mistake each: no permission filter at serving. The
   Recommendation playbook already had it. Not a catalog item.
4. **Other entries.** Declined: the sampled-ratio metric floor, the
   embedding index version, the 2 Quick-budget sources, versioned file
   names. Deferred: rules for a text-only mixed report.

## Consequences

- Part 4 of a critique is longer. Quick mode still limits it to 5
  questions.
- Fewer log entries, each with a failure behind it. A real gap that
  caused no failure in a run is not logged until it does.
- User-requested entries are not filtered.
