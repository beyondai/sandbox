# ML critique is one core skill with 2 lenses and 2 modes

## Context

The `ml-*` skills write design docs and modeling reports. No skill judged
the quality of a finished write-up:

- The Review mode of each section skill examines coverage only ("is each
  item answered, not just headed").
- `grilling` asks questions to make a plan. It does not judge a finished
  plan.
- `ml-modeling-evaluate` examines numbers. It does not examine the
  reasoning that made them.

A write-up can have all its sections and still fail: a metric that does not
match the decision, a label that leaks, a random split on time data, no
fallback. The user wants the review that a very experienced ML system
designer gives. That reviewer finds the obvious mistakes quickly, and knows
the standard solutions. Then the user and the reviewer settle each finding
and record the decisions and the trade-offs.

## Decision

```
 ml-critique (core: persona, modes, 4 parts, converge, done, playbooks)
   |-- ml-critique-system    (lens: catalog A-K for design write-ups)
   '-- ml-critique-modeling  (lens: catalog A-K for modeling reports)
```

1. **3 skills.** `ml-critique` is the core and the router.
   `ml-critique-system` and `ml-critique-modeling` are lenses. Each lens
   holds only what to look for (its catalog) and its rules for evidence.
2. **4-part critique.** What was done well, what to change or fix, what is
   missing, and questions for the original design. The questions include
   the questions that the designer did not ask, each with an expected answer
   from experience.
3. **Reviewer persona and playbooks.** The reviewer identifies the problem
   type, and uses a playbook (`ml-critique/references/playbooks.md`) with
   the standard framing, architecture, baseline, metrics, classic mistakes,
   and questions. Each part-2 and part-3 finding must name a proven
   alternative. A finding with no alternative becomes a question.
4. **Cold reader.** Each lens runs in a new subagent. The session that wrote
   the write-up knows the intent, and reads the intent, not the text.
5. **Priority, not only severity.** A chief architect spends the review
   time where it changes the result most. Each finding gets P1 (vague or
   wrong at the core: problem, label, metric, model, baseline, leakage,
   split), P2 (a large gain in performance, cost, or time), or P3 (small).
   Upstream findings come before downstream findings, because an error in
   the problem makes all later work wrong. The summary starts with the top
   3 changes. Brief mode shows P1 and P2 only.
6. **Converge with `grilling`.** Each finding gets a resolution: accept,
   modify, reject, or defer.
7. **Definition of done.** Each finding has a resolution. Each decision has
   its trade-off. Each deferred item has a reason, an owner, an unblock
   condition, and a risk. A conclusion gives a verdict. The user confirms.
8. **2 modes, selected by keyword.** Brief (45 minutes, caps for each
   part, `[C]` catalog items, P1 and P2 only, 2 rounds maximum, no
   checkpoints) and Normal (a few hours, the full catalog, command evidence
   for the modeling lens, checkpoints at each phase and round). In Normal
   mode, the user can go to the next step at a checkpoint. Then all open
   items go to Deferred with the reason "the user went to the next step".
9. **Output.** One file, `<project-folder>/critique/<date>-<lens>.md`, or
   `critique/<date>-<slug>.md` in the write-up's folder with no project
   folder (never `notes/`, which holds only user-written content). The
   critique does not edit the write-up.

10. **Optional reference design.** The user can give their own design at
    any phase. The skill asks for it once at the start, and never searches
    for one, because a fresh view is sometimes the goal. A separate
    subagent compares it with the write-up after the lens runs, so the
    lens view stays independent. The reference is one more opinion, not
    the truth.

## Considered options

- **One critique skill for each design section (9 skills).** Rejected. The
  worst errors cross sections (the PRD metric is not the evaluated metric),
  and a critic for one section does not see them. It also copies the
  procedure 9 times.
- **One skill with system and modeling together.** Rejected. The 2 lenses
  need different knowledge and different evidence: the system lens judges
  reasoning, and the modeling lens proves findings with code and data. One
  file with both catalogs is too long, and each run uses only part of it.
- **Brief and Normal as separate skills.** Rejected. They have the same
  procedure and the same catalogs. Only the depth and the pace change. A
  keyword mode is the same convention as Quick-POC and Regular (0001).
- **Add quality checks to the existing Review modes.** Rejected. Review mode
  is a fast coverage check during drafting. Critique is a separate, deeper
  pass on a finished write-up, with a convergence loop and an output file.
- **Critique in the same session that wrote the write-up.** Rejected as the
  default. That session reads its own intent into the text.

## Consequences

- The catalogs and the playbooks are the reviewer's experience. Add to them
  when a real critique finds a new pattern. Use the skill improvement log
  (0004).
- The modeling lens runs probes in Normal mode. The probes run in the
  scratchpad, and they do not change the project.
- The new skills and the `ml-system-design` "Output docs" section use
  approximately 80% of ASD-STE100, with ASCII diagrams next to the text
  where they help.
