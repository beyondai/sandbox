# ML Critique Guide

## Contents

- [What the skills do](#what-the-skills-do)
- [The procedure](#the-procedure)
- [Priority](#priority)
- [Checkpoints](#checkpoints)
- [Critique context](#critique-context)
- [Merge and share-out](#merge-and-share-out)
- [Examples](#examples)
  1. [A review of a full project](#1-a-review-of-a-full-project)
  2. [A review of the modeling only, with
     proof](#2-a-review-of-the-modeling-only-with-proof)
  3. [A review of the design only](#3-a-review-of-the-design-only)
  4. [Compare with your own design from the
     start](#4-compare-with-your-own-design-from-the-start)
  5. [Add your design during the
     discussion](#5-add-your-design-during-the-discussion)
  6. [Stop early](#6-stop-early)
  7. [Answer in a notes file](#7-answer-in-a-notes-file)
  8. [Review a pasted interview answer](#8-review-a-pasted-interview-answer)
  9. [Critique with a context](#9-critique-with-a-context)
  10. [After the critique](#10-after-the-critique)
  11. [Merge 2 critiques](#11-merge-2-critiques)
  12. [Prepare a share-out](#12-prepare-a-share-out)
- [Where files go](#where-files-go)
- [Tips](#tips)

This guide tells you how to use the `ml-critique` skills, with examples.
- Skill files: `.agents/skills/personal/ml-critique*/`.
- The reasons for the design: `adr/0009-ml-critique-skills.md`,
  `adr/0018-critique-coverage-quick-mode-and-context.md`, and
  `adr/0020-critique-merge-share-out-one-mode.md`.
- The principles that the review applies:
  `.agents/skills/personal/ml-design-principles.md`.

## What the skills do

You give a finished ML write-up. The skills review it as a chief ML
architect, and show the most important problems first. Then they work with
you until each problem has a decision. They record the decisions and the
trade-offs.

There are 5 skills:
- **`ml-critique`**: the entry point. It asks for the view and the
  context, selects the lens, and runs the full procedure.
- **`ml-critique-system`**: the system lens. It reviews the goal,
  metrics, requirements, team, framing, labels, data, features,
  architecture, phasing, serving, delivery, and post-delivery.
- **`ml-critique-modeling`**: the modeling lens. It reviews the baseline,
  dataset, data profile, split, leakage, features, model, training setup,
  tuning, evaluation, serving, and reproducibility.
- **`ml-critique-merge`**: joins 2 or more critiques of one write-up into
  one final critique.
- **`ml-critique-share-out`**: turns a final critique into a share-out
  plan: what to discuss, in which order, in a fixed time.

The 2 lenses check each key decision and step of the `ml-system-design-*`
and `ml-modeling-*` skills. The map from each skill item to its checks:
`.agents/skills/personal/ml-critique/references/coverage.md`.

Use `ml-critique` in most cases. It calls the correct lens. Each lens skill
also works alone, when you want only one view.

```
 ml-critique (1 or more runs) --> critique/<date>-<lens>.md
                                        |
                          ml-critique-merge (2+ critiques)
                                        v
                          critique/<date>-final.md
                                        |
                          ml-critique-share-out (+ share-out context)
                                        v
                          critique/<date>-share-out.md
```

Use a different skill for these tasks:
- To **write** a design: `ml-system-design` or `ml-modeling`.
- To check that each section is **present**: the Review mode of the
  section skill.
- To **make** a plan by interview: `grilling`.

## The procedure

```
 write-up (file | pasted text | project folder)
      |
      v
 1 Select     asks 2 questions, waits for the answers:
              view (Fresh | With my design),
              critique context (path | text | none)
              + lens, problem type
      v
 2 Critique   lens in a new subagent -> 4 parts, most important first
      v
 3 Converge   rounds of questions -> accept | modify | reject | defer
      v
 4 Document   <project>/critique/<date>-<lens>.md
      v
 5 Check      intent questions + check_doc.py, fix, log skill issues
```

1. **Select.** The skill selects the lens from the content and the
   problem type (churn, recommendation, fraud, and other types). For one
   file, it selects the lens from the file's sections. A file with design
   and results content gets both lenses, and each lens owns its sections.
   Then it asks 2 questions in one message, and waits for your answers:
   1. **View:** Fresh (no reference) or With my design (give a path).
   2. **Critique context:** what the critique is for, or "none".

   It does not ask a question that your words already answered.
2. **Critique.** Each lens runs in a new subagent. Thus, it reads the text
   and not the intent of the author. It checks the full catalog. It gives
   4 parts:
   1. **Done well:** what to keep. Only strengths that are costly to
      lose, at most 5, each with what breaks if it is lost. No basic
      hygiene (0020).
   2. **Change or fix:** each item with a priority, evidence, the effect,
      and an alternative.
   3. **Missing:** each item with the standard method.
   4. **Questions:** clarifications, and the questions that the designer
      did not ask. Each one has an expected answer, why it matters, and
      what each answer changes. A vague claim gets an "in which sense?"
      question (0019).
3. **Converge.** The skill asks numbered questions, P1 first. Each
   question has a recommended answer. You answer each one:
   - **accept**;
   - **modify**;
   - **reject** (give a reason);
   - **defer** (give an owner and the condition that unblocks it).

   A new item that you add (a strength, a change, a question) gets the
   tag `[user]`. Thus, the file shows who found what (0020).
4. **Document.** The skill writes one file. The file has the context, the
   4 parts, the decisions and trade-offs, the deferred items, and a
   verdict: `ready`, `ready with changes`, or `needs rework`.
5. **Check.** The skill reads the file again:
   - Does each P1 and P2 item have evidence and an alternative?
   - Are the top 3 changes single changes, sorted by importance?
   - Does each item have a decision or a Deferred entry?
   - Does the verdict follow from the decisions?
   - Is each context conflict in the Context section?
   - Is each new item of yours tagged `[user]`, and does each strength
     say what breaks if it is lost?

   It also runs `check_doc.py` on the file. It fixes the file and checks
   again, at most 2 times.

## Priority

- **P1: vague or wrong at the core.** Examples: the problem is not clear;
  a wrong label, metric, or model family; no real baseline; leakage; a
  split that is not like production.
- **P2: a large gain.** Examples: better performance, lower cost, a
  stronger baseline, a simpler design with the same result.
- **P3: a small gain.** Examples: polish, small gaps.

The skill sorts findings with one key, in this order:
1. Priority: all P1, then all P2, then all P3.
2. Upstream first. An error in the goal or the label makes all later work
   wrong.
3. The larger effect first.
4. The finding that the skill is more sure of first.

The skill also checks in importance order: the playbook's classic
mistakes first, then the catalog sections in order. Inside a section, the
classic-mistake items come first. The summary starts with the top 3
changes. Each one is a single change.

The review applies Principle 1: simple by default, complex only with
evidence. A complex model that wins by less than the noise, or that costs
more than its gain is worth, is a P2 finding.

## Checkpoints

There is one mode. Each run checks the full catalog, because the agent
part takes minutes (0020).
- Evidence: command output (probes) for each modeling P1 and P2. For a
  text-only write-up (no code or data), a quote and a shown calculation.
- Findings: all, P1 to P3.
- Converge: rounds until no item is open. A checkpoint after each phase
  and each round.

At a checkpoint, you can say "next step". The open items then go to
Deferred. Nothing is lost.

## Critique context

A critique context tells the skill what the critique is for. Examples: an
interview brief with required topics, a review for a launch decision.

- The skill asks for it in each run. Give a file path, text, or "none".
- With no context, the skill follows its general rules.
- With a context, the general rules still apply. The context wins only
  when the 2 conflict.
- The skill notes each conflict, each time: in chat when it happens, and
  in the "Context" section of the critique file (the rule, the context
  requirement, and what was done).
- A time limit ("prepare in less than 2 hours") is not a conflict. It is
  your share-out time. The critique runs in full and records the limit
  for `ml-critique-share-out`.
- The lenses get the context. It says what to cover, not what the answer
  is, so the view stays fresh.

## Merge and share-out

**`ml-critique-merge`** joins independent critiques of one write-up (2
runs, a run and a colleague's review).
- It joins the items that are the same problem, and keeps the stronger
  evidence.
- A different priority, claim, or decision between the sources becomes a
  question for you, with a recommended answer.
- It keeps the `[user]` and `[ref]` tags and each source decision. A
  rejected item goes to a Rejected section.
- It discusses with you in rounds. It writes nothing until you say
  "write".
- Output: `critique/<date>-final.md`. The sources do not change.

**`ml-critique-share-out`** prepares what to say in a fixed time.
- Input: one final critique and a share-out context (an interview brief,
  a meeting). With several critiques, it runs `ml-critique-merge` first.
- It reads the share-out limit, the format, the required topics, and the
  audience from the context.
- It proposes a timeline with about 20% free time, talking points in
  priority order, the questions to ask, a backup list, and a cut list.
- It never cuts a P1. Each required topic gets a point if the P1 points
  leave time. If not, the skill tells you which topic has no point
  (0021).
- Each talking point has a claim, the evidence, the alternative, a sketch
  when it helps, and the likely follow-up questions with answers.
- It adds delivery notes for the context type: a working-session
  interview, a team design review, or a launch review.
- It discusses with you in rounds. It writes nothing until you say
  "write".
- Output: `critique/<date>-share-out.md`. The critique does not change.

## Examples

### 1. A review of a full project

```
/ml-critique labs/proj1
```

What happens:
1. The skill says: "Lenses: system and modeling. Problem type: churn and
   retention." It asks: "View: fresh, or with your design? Critique
   context: a path, text, or none?" You answer "fresh, none".
2. The 2 lenses run in parallel. You get the top 3 changes and the 4
   parts.
3. Round 1 has the P1 items. Round 2 has the P2 items. A question looks
   like this:

   ```
   ❓ Q3 - Scoring population: the code keeps players who already left
   (build_dataset.py:106). Precision@20% = 0.997. Score only players
   active in (90, 120]?

   ➡️ Accept. The current metric measures players who are already gone.
   ```

4. The skill writes `labs/proj1/critique/2026-10-08-both.md`.

### 2. A review of the modeling only, with proof

```
critique the modeling in labs/proj1
```

For each P1 and P2 finding, the modeling lens runs a small probe in the
session scratchpad. It never changes your project. A typical finding:

```
P1. contract_end_flag is target leakage.
- Evidence: engineer_features.py:28 uses Churn. Probe: the flag is 1 for
  100% of churners; test AUC goes from 0.9155 to 0.9390 with it.
- Alternative: remove it, and add a guard that fails when the label is an
  input to the feature code.
```

### 3. A review of the design only

```
/ml-critique-system labs/proj1
```

Use this before modeling starts, or when you want only the system view.
It reads `prd/`, `design/`, and `adr/`.

### 4. Compare with your own design from the start

When the skill asks for the view, answer:

```
with my design: ~/work/my-churn-design.md
```

The lens reviews the write-up without the reference first. Then a
separate reference pass compares the 2 designs. Its items have the tag
`[ref]`. The reference is one more opinion, not the truth. The skill also
says where the write-up is better than your design.

### 5. Add your design during the discussion

During Converge, say:

```
here is my own design for this: labs/proj1-mine/design/high-level.md
```

The new `[ref]` items join the open questions, sorted by importance. If a
`[ref]` P1 item contradicts a decision that you made, the skill asks if
you want to reopen that decision.

The skill uses a reference design only when you give one. It never
searches for one.

### 6. Stop early

At a checkpoint, say:

```
go to the next step
```

Each open item goes to Deferred with the reason "the user went to the
next step". Each one has an owner, an unblock condition, and a risk.

### 7. Answer in a notes file

For long answers, write them in your notes file, and point to it:

```
answers are in @notes/proj1.md under #critique
```

The skill reads only the new content. It says which questions the new
content answered.

### 8. Review a pasted interview answer

Paste the answer, then say:

```
critique this ML system design interview answer
```

There is no project folder, so the skill asks where to save the critique.
The questions in part 4 are the follow-up questions that an interviewer
would ask.

### 9. Critique with a context

```
/ml-critique labs/ml-riot-wiki-recommender-1/interview/original-design-to-review.md
```

When the skill asks, answer:

```
fresh; context: labs/ml-riot-wiki-recommender-1/interview/instructions.md
```

The file has design and results content, so both lenses run. The
context asks for 4 topics (done well, change, missing, questions to the
author). They are the same as the 4 parts, so there is no conflict. The
context also says "prepare in less than 2 hours". That is the share-out
time, not a conflict: the Context section records it for the share-out.

### 10. After the critique

- The skill offers an ADR for each decision that is difficult to reverse.
- If the write-up came from the `ml-*` skills, it offers to send each
  accepted fix to the skill that owns it. Example: a leakage fix goes to
  `ml-modeling-features`. Then the later steps run again.
- It offers `ml-critique-merge` if another critique of the same write-up
  exists, and `ml-critique-share-out` if the critique is for a share-out.

### 11. Merge 2 critiques

```
/ml-critique-merge labs/ml-riot-wiki-recommender-1/critique/2026-10-09-both-v1.md labs/ml-riot-wiki-recommender-1/critique/2026-10-09-both-v2.md
```

The skill asks for the critique context, then shows the merged parts,
the Rejected list, and each disagreement as a question. Example of a
disagreement:

```
❓ D1 - Label learns the link graph: v1 says P1, v2 says P2.
➡️ P1. A wrong label is a P1 example in the Priority table.
```

Say "write" when you are done. The skill writes
`critique/2026-10-09-final.md`.

### 12. Prepare a share-out

```
/ml-critique-share-out labs/ml-riot-wiki-recommender-1/critique/2026-10-09-final.md Context: labs/ml-riot-wiki-recommender-1/interview/instructions.md
```

The skill reads the limit (about 45 minutes of discussion), the 4
required topics, and "be ready to sketch". It selects the type
"working-session interview" and proposes a timeline:

```
 0      2        5          15            28          36    45
 |-top3-|-credit-|-change P1-|-change P2+M-|-questions-|-free-|
```

Change the order or the points in rounds. Say "write" when you are done.
The skill writes `critique/2026-10-09-share-out.md`.

## Where files go

```
labs/proj1/                 (the parent is labs/ unless you name another)
  critique/2026-10-08-both.md
  critique/2026-10-09-modeling.md
  critique/2026-10-09-final.md       (ml-critique-merge)
  critique/2026-10-09-share-out.md   (ml-critique-share-out)
```

- A critique file name ends in the lens: `system`, `modeling`, or `both`.
  If the file exists, the skill adds `-v<N>`.
- No skill edits your write-up. The merge and the share-out do not edit
  their input critiques.
- With no project folder, the file goes in `critique/` in the folder of
  the write-up. For pasted text, the skill asks where to write it.
- Nothing goes in `notes/`. That folder is only for your own content.

## Tips

- For a fair review, start with a fresh view. Add your own design later
  if you want a comparison.
- For an interview or a meeting, run the full critique, then the
  share-out. The share-out cuts for time, not the critique.
- Give a context when the critique has a purpose with its own demands,
  for example an interview brief.
- A skill problem found during a run goes to the shared
  `.agents/skills/personal/SKILL-IMPROVEMENTS.md`. The skill does not
  change itself during the run. It logs a problem only if the problem
  made the critique worse (0019).
