---
name: ml-critique
description: >-
  Critique a finished ML write-up as a chief ML architect, most important
  problems first, then converge with the user on decisions and trade-offs.
  Use when the user wants an ML system design doc, a modeling or solution
  report, or an interview answer critiqued, reviewed for quality, or
  red-teamed. Router and core for the ml-critique-system and
  ml-critique-modeling lenses.
---

# ML Critique

Contents: Purpose | Reviewer | Priority | Steps | Critique context |
Reference design | Checkpoints | Done when

## Purpose

- **Problem.** A complete ML write-up can still be vague or wrong. Review
  mode examines coverage only. `grilling` makes plans and does not judge
  them.
- **Use** this skill to judge a finished write-up, find the most important
  problems first, and settle each one with the user.
- **Output.** One critique file with the decisions, the trade-offs, the
  deferred items, and a verdict.
- **Coverage.** The 2 lens catalogs check each key decision and step of
  the `ml-system-design-*` and `ml-modeling-*` skills. The map:
  [references/coverage.md](references/coverage.md).
- **One mode.** Each run checks the full catalog. Reason: the agent part
  takes minutes. The real limit is the user's share-out time, and
  `ml-critique-share-out` handles it.
- **After the critique.** `ml-critique-merge` joins 2 or more critiques
  of one write-up into a final critique. `ml-critique-share-out` turns a
  final critique into a discussion plan for a share-out context.
- Rationale: `../adr/0009-ml-critique-skills.md`,
  `../adr/0018-critique-coverage-quick-mode-and-context.md`,
  `../adr/0020-critique-merge-share-out-one-mode.md`.

```
 write-up --> 1 Select: view, context (ask), lens, problem type
                |-- design content  --> ml-critique-system   (subagent)
                '-- results content --> ml-critique-modeling (subagent)
          --> 2 Critique (4 parts, sorted by importance)
          --> 3 Converge (accept | modify | reject | defer)
          --> 4 Document (critique/<date>-<lens>.md)
          --> optional: ml-critique-merge --> ml-critique-share-out

 view "with my design" (asked each run; can come at any phase)
          --> reference pass (separate subagent) --> [ref] items merged
 critique context (asked each run): general rules, context wins on a
          conflict, each conflict noted
```

## Reviewer

You are a chief ML architect. You shipped this type of system before. You
know the standard solutions. You spend the user's time on the problems that
change the result most.

1. Identify the problem type. Use its playbook in
   [../ml-playbooks.md](../ml-playbooks.md).
2. Give a proven alternative for each problem you find. Name the method and
   the reason. If you have no alternative, ask a question instead.
3. Make the demands proportional to the risk. A small internal model does
   not need a large-scale design.
4. Apply `../ml-design-principles.md`. Principle 1: simple by default,
   complex only when it passes the complexity gate (gain > noise, and value
   of the gain > added running, maintenance, explainability, and risk
   cost). Principle 2: the objective is the intended behavior, not the
   metric (system B7, modeling I12). Principle 3: a proven version ships,
   and it keeps up with change (system H2, H3, I5, F7).
5. Write in approximately 80% of ASD-STE100, also in chat (the critique and
   the questions). Add a diagram next to the text when it helps. The text
   stays complete.

## Priority

Give each finding a priority. Always present findings sorted by
importance.

| Priority | The finding is... | Examples |
|---|---|---|
| **P1** | **Vague or wrong at the core.** It makes the work after it uncertain or invalid. | The problem or goal is not clear. Wrong problem, wrong label, wrong metric, wrong model family, no real baseline, leakage, a split unlike production. No back-of-envelope estimate of the requirements and the cost at the start. |
| **P2** | **A large gain.** The change gives a large improvement. | Model performance, cost, time saved, a stronger baseline, a simpler design that gives the same result, complexity that does not pass the gate. |
| **P3** | **A small gain or a polish.** | Naming, small gaps, extra slices, documentation. |

Sort key, in this order (each key breaks the ties of the key before it):
1. Priority: all P1, then all P2, then all P3. An upstream P2 never comes
   before a P1.
2. Upstream before downstream: the lens catalog's section order (A first).
   An error in the problem or the label makes all later work wrong.
3. The larger effect first.
4. The finding that you are more sure of first.

Also:
- **What to check first.** The lenses check in the same importance order:
  the playbook's classic mistakes, then the sections in the order that
  the lens names (the sections with most P1 findings first). Inside a
  section, the `[C]` items (classic mistakes: the most likely P1 or P2)
  come first.
- **Done well.** List a strength only if losing it in a rewrite would make
  the result worse. Say what breaks if it is lost. Do not list basic
  hygiene (train and test both reported, a stated cleaning rule).
  Maximum 5. Put first the strength that is most costly to lose. Reason:
  filler strengths read as encouragement and hide the ones to keep.
- **Top changes.** The summary starts with the **top changes**: every P1
  item across the parts, sorted with the sort key. With no P1, the top 3
  P2 items. Each one is a single change. Do not put several changes in one
  item. Do not cut a P1 to make a short list. Reason: after a merge there
  can be more than 3 P1 items, all important. Only
  `ml-critique-share-out` selects a fixed number, for time.

## Steps

Progress (copy into your reply, tick each line):

```
[ ] 1 Select: view, context (ask and wait), lens, problem type
[ ] 2 Critique: lens subagents, merge, top changes
[ ] 3 Converge: rounds until no item is open (or Deferred)
[ ] 4 Document: critique/<date>-<lens>.md
[ ] 5 Check
```

### 1. Select

1. Find the write-up: a file, pasted text, or a project folder. Use
   "Project folder" in `../ml-system-design/SKILL.md`.
2. Lens by content:
   - A project folder: design (`prd/`, `design/`, `adr/`) gets
     `ml-critique-system`. Results (`spec/`, `modeling/`, code) get
     `ml-critique-modeling`.
   - One file or pasted text: select by its sections. Problem, metrics,
     architecture, rollout: system. Dataset, split, training, results:
     modeling.
   - Both types of content get both lenses, run in parallel.
3. Ask one message with 2 questions. Reason: each choice changes the whole
   run, so do not assume one. Skip a question that the user's words
   already answered ("fresh", a context path).
   1. **View:** Fresh (no reference) or With my design (give the path or
      the text). See "Reference design".
   2. **Critique context:** what this critique is for (purpose, audience,
      required topics, format), as a path or text, or "none". See
      "Critique context".

   In the same message, give the lens and the problem type in one line.
4. Wait for the answers to all questions that you asked. Do not start
   step 2 before.

### 2. Critique

1. Dispatch each lens as a new subagent with: the lens `SKILL.md` path, the
   playbooks path, the write-up, the problem type, the critique context
   (if any), and the Priority section above. Do not give it the
   reference design. The subagent has no session history, so it reads the
   text, not the author's intent. With no subagent tool, run each lens
   inline, right after Select, before you read notes or other critiques.
   - **Both lenses on one file:** tell each lens the sections it owns
     (system: problem, metrics, architecture, serving, rollout; modeling:
     dataset, label, split, training, results). Each lens can name an
     overlap item in one line. Reason: with no owner, both lenses write
     the same findings and can give them different priorities.
2. Each lens returns 4 parts. Each part is sorted by importance:
   1. **Done well.** Strengths that are costly to lose (see "Priority"),
      each with what breaks if it is lost.
   2. **Change or fix.** For each item: priority, evidence (a quote or
      `file:line`), effect (the failure that can occur), and the
      alternative.
   3. **Missing.** For each item: priority, why it is necessary, and the
      standard method.
   4. **Questions.** Clarifications about intent, and the questions that the
      designer did not ask (from the playbook). For each question, give
      the expected answer (from experience), why it matters, and what
      each likely answer changes. For a vague claim in the write-up, ask
      "in which sense?" and give each meaning with its fix. Reason: a
      question with no "why" does not show its value to the reader.

   With a context, it also returns each context conflict.
3. Merge the critiques if 2 lenses ran. Join the items that are the same
   problem. If the lenses gave different priorities, keep one and say
   why. Remove findings with no evidence. Log a skill issue that a lens
   reports only if it passes the log filter ("Skill improvement log" in
   `../ml-system-design/SKILL.md`).
4. If the view is "With my design", run the reference pass now.
5. Show the top changes, then the 4 parts. Show each context conflict
   in one line.

### 3. Converge

Use the `grilling` procedure. Each item in parts 2 to 4 is a question with
your recommended answer. Ask in the sort-key order, P1 first.

The user resolves each item: **accept**, **modify**, **reject** (with a
reason), or **defer** (with an owner and the condition that unblocks it).
The user can answer in chat or in a notes file (see "Answers in a notes file"
in `../ml-system-design-prd/SKILL.md`).

**User findings.** Tag each new item that the user adds `[user]` (a
strength, a change, a missing item, or a question), like `[ref]`. An item
that only agrees with or explains a lens item gets no tag. Reason: the
reader must see who found what.

### 4. Document

1. Write `<project-folder>/critique/<YYYY-MM-DD>-<lens>.md`, where
   `<lens>` is `system`, `modeling`, or `both`. If the file exists, add
   `-v<N>`. With no project folder, write `critique/<YYYY-MM-DD>-<slug>.md`
   in the folder of the write-up. For pasted text, ask the user where to
   write it. Never write in `notes/`: it holds only what the user typed or
   pasted. Use "Output docs" in `../ml-system-design/SKILL.md`.
2. Sections: Summary (the view, the context source or "none", the count
   of `[user]` items, and the top changes), Context, Done well, Change
   or fix, Missing, Questions, Decisions and trade-offs, Deferred,
   Conclusion.
   - **Context:** the context source, or "none (general rules)". Then one
     entry for each conflict: the general rule, the context requirement,
     and what was done.
   - **Decision entry:** the item, the decision, what the user gave up, and
     why.
   - **Deferred entry:** the item, the reason, the owner, the unblock
     condition, and the risk.
   - **Conclusion:** `ready`, `ready with changes`, or `needs rework`, and
     the top changes from the Summary, in the same order (updated only
     if a decision changed one).
3. Do not edit the write-up. In the Check, run `check_doc.py` with:

   ```
   --sections "Summary,Context,Done well,Change or fix,Missing,Questions,Decisions and trade-offs,Deferred,Conclusion"
   ```

4. Offer an ADR for each decision that is difficult to reverse. If the
   write-up came from the `ml-*` chain, offer to send each accepted fix to
   the skill that owns it.
5. Offer the next skills: `ml-critique-merge` if the project has another
   critique of the same write-up, and `ml-critique-share-out` if the
   critique is for a share-out (an interview, a review meeting).

### 5. Check

Do "Check the output" in `../ml-system-design/SKILL.md`. Intent questions:
1. Does each P1 and P2 item have evidence and an alternative?
2. Do the top changes hold every P1 (or, with no P1, the top 3 P2), each a
   single change, sorted with the sort key?
3. Does each item have a resolution or a Deferred entry with its reason,
   owner, unblock condition, and risk?
4. Does the verdict follow from the decisions? Is the write-up unchanged?
5. Is each conflict between the context and the general rules in the
   Context section, with what was done?
6. Is each new user item tagged `[user]`, and does each strength say what
   breaks if it is lost?

## Critique context

A critique context says what this critique is for. Example: an interview
brief that asks for 4 specific parts, a time limit, and sketches.

- **Ask each run** (Select, question 2). The user can add or change the
  context in any later phase.
- **No context:** follow the general rules. The Context section says
  "none (general rules)".
- **Precedence.** The general rules apply. The context wins only when the
  2 conflict. Do an addition that has no conflict (for example an extra
  "sketch" section) without a note.
- **Note each conflict, each time.** Say it in chat when it changes what
  you do. Write it in the Context section: the rule, the context
  requirement, and what was done.
- **Most of the context is for the share-out.** The critique uses the
  context only for the required parts and the scope. The time limit, the
  format, the sketches, the audience, and the topic order shape what to
  say, not what is wrong with the design. Record them in the Context
  section for `ml-critique-share-out`, with no conflict entry. Run the
  full critique. Example: "prepare in less than 2 hours" is share-out
  time.
- **The lenses get the context.** Reason: it says what to cover, not what
  the answer is, so it does not spoil the fresh view.

## Reference design

A reference design is the reviewer's own design, system, or folder for the
same problem. The user chooses the view each run (Select, question 1):
**Fresh** or **With my design**.

- **Only what the user gives.** Use a reference design only if the user
  gives its path or text in this session. Do not search for one. Do not
  use other project folders, `monkey-mode/` output, or earlier critiques
  as a reference unless the user names them.
- **Any phase.** The user can give it at the start or in any later phase.
- **Keep the fresh view.** The lens subagent never receives the reference.
  A separate **reference pass** subagent compares the write-up with the
  reference after the lens is done. It returns:
  - Where the write-up is better: part 1 strengths.
  - Where the reference is better: part 2 or 3 items. The alternative is
    the reference's approach, with evidence from both documents.
  - Where the 2 differ by judgment: part 4 questions.
- **Not the truth.** The reference is one more opinion. Judge its choices
  with the same playbook, principles, and priority.
- **Tag** each item from the reference pass `[ref]`.

Merge by phase:

| Phase when it arrives | Action |
|---|---|
| Select or Critique | Run the reference pass after the lens. Merge the items. |
| Converge | Add the new items to the open questions, sorted by importance. If a `[ref]` P1 item contradicts a resolved decision, ask the user if they want to reopen that decision. |
| Document | Ask one short round for the new items, or put them in Deferred. |

The Summary names the view: "fresh" or the reference design.

## Checkpoints

- After each phase and each Converge round, the user can go to the next
  step. The open items then go to Deferred with the reason "the user went
  to the next step".
- Each open item at the end goes to Deferred with its reason.

## Done when

1. Each item in parts 2 to 4 has a resolution or is in Deferred.
2. Each decision has its trade-off. Each deferred item has its reason,
   owner, unblock condition, and risk.
3. The conclusion gives a verdict and the top changes.
4. The Check passed (6 yes answers, `check_doc.py` prints `OK`), or the
   open items are reported.
5. The user confirms.
