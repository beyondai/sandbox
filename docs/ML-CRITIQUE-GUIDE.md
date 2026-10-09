# ML Critique Guide

## Contents

- [What the skills do](#what-the-skills-do)
- [The procedure](#the-procedure)
- [Priority](#priority)
- [Modes](#modes)
- [Examples](#examples)
  1. [A quick review of a full project](#1-a-quick-review-of-a-full-project)
  2. [A full review of the modeling only, with
     proof](#2-a-full-review-of-the-modeling-only-with-proof)
  3. [A review of the design only](#3-a-review-of-the-design-only)
  4. [Compare with your own design from the
     start](#4-compare-with-your-own-design-from-the-start)
  5. [Add your design during the
     discussion](#5-add-your-design-during-the-discussion)
  6. [Stop early in Normal mode](#6-stop-early-in-normal-mode)
  7. [Answer in a notes file](#7-answer-in-a-notes-file)
  8. [Review a pasted interview answer](#8-review-a-pasted-interview-answer)
  9. [After the critique](#9-after-the-critique)
- [Where files go](#where-files-go)
- [Tips](#tips)

This guide tells you how to use the `ml-critique` skills, with examples.
- Skill files: `.agents/skills/personal/ml-critique*/`.
- The reasons for the design: `adr/0009-ml-critique-skills.md`.
- The principles that the review applies:
  `.agents/skills/personal/ml-design-principles.md`.

## What the skills do

You give a finished ML write-up. The skills review it as a chief ML
architect, and show the most important problems first. Then they work with
you until each problem has a decision. They record the decisions and the
trade-offs.

There are 3 skills:
- **`ml-critique`**: the entry point. It selects the mode and the lens,
  and runs the full procedure.
- **`ml-critique-system`**: the system lens. It reviews the goal,
  metrics, framing, labels, data, architecture, phasing, serving, and
  delivery.
- **`ml-critique-modeling`**: the modeling lens. It reviews the baseline,
  dataset, split, leakage, features, model, training setup, evaluation,
  and serving.

Use `ml-critique` in most cases. It calls the correct lens. Each lens skill
also works alone, when you want only one view.

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
 ml-critique: mode (Brief | Normal), lens, problem type
      |   asks: "compare with a reference design of your own?"
      v
 1 Critique   lens in a new subagent -> 4 parts, P1 first
      v
 2 Converge   rounds of questions -> accept | modify | reject | defer
      v
 3 Document   <project>/critique/<date>-<lens>.md
      v
 4 Check      intent questions + check_doc.py, fix, log skill issues
```

1. **Select.** The skill selects the mode from your words, the lens from
   the content, and the problem type (churn, recommendation, fraud, and
   other types). It asks one question: do you want to compare with a
   reference design of your own? The default is "no", for a fresh view.
2. **Critique.** Each lens runs in a new subagent. Thus, it reads the text
   and not the intent of the author. It gives 4 parts:
   1. **Done well:** what to keep.
   2. **Change or fix:** each item with a priority, evidence, the effect,
      and an alternative.
   3. **Missing:** each item with the standard method.
   4. **Questions:** clarifications, and the questions that the designer
      did not ask, each with an expected answer.
3. **Converge.** The skill asks numbered questions, P1 first. Each
   question has a recommended answer. You answer each one:
   - **accept**;
   - **modify**;
   - **reject** (give a reason);
   - **defer** (give an owner and the condition that unblocks it).
4. **Document.** The skill writes one file. The file has the 4 parts, the
   decisions and trade-offs, the deferred items, and a verdict: `ready`,
   `ready with changes`, or `needs rework`.
5. **Check.** The skill reads the file again:
   - Does each P1 and P2 item have evidence and an alternative?
   - Are the top 3 changes single changes, in priority order?
   - Does each item have a decision or a Deferred entry?
   - Does the verdict follow from the decisions?

   It also runs `check_doc.py` on the file. It fixes the file and checks
   again, at most 2 times.

## Priority

- **P1: vague or wrong at the core.** Examples: the problem is not clear;
  a wrong label, metric, or model family; no real baseline; leakage; a
  split that is not like production.
- **P2: a large gain.** Examples: better performance, lower cost, a
  stronger baseline, a simpler design with the same result.
- **P3: a small gain.** Examples: polish, small gaps.

Upstream problems come first. An error in the goal or the label makes all
later work wrong. The summary starts with the top 3 changes. Each one is a
single change.

The review applies Principle 1: simple by default, complex only with
evidence. A complex model that wins by less than the noise, or that costs
more than its gain is worth, is a P2 finding.

## Modes

**Brief** (keywords: "brief", "quick", "45 min"):
- Time: about 45 minutes, with no checkpoints.
- Findings: P1 and P2 only. At most 5 for each part, and 3 strengths. A
  limit never removes a P1.
- Modeling evidence: code lines and existing output. The lens can read
  any file. It runs no probes.
- Converge: 2 rounds of 6 questions, P1 first, then P2. Items that do not
  fit go to Deferred, with the reason "no time".

**Normal** (all other requests):
- Time: a few hours.
- Findings: all, P1 to P3.
- Modeling evidence: command output (probes) for each P1 and P2.
- Converge: rounds until no item is open. A checkpoint after each phase
  and each round.

In Normal mode, you can say "next step" at a checkpoint. The open items
then go to Deferred. Nothing is lost.

## Examples

### 1. A quick review of a full project

```
/ml-critique brief labs/proj1
```

What happens:
1. The skill says: "Mode: Brief. Lenses: system and modeling. Problem
   type: churn and retention. Do you want to compare with a reference
   design of your own? Default: no, a fresh view." You answer "no".
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

### 2. A full review of the modeling only, with proof

```
critique the modeling in labs/proj1
```

The modeling lens runs in Normal mode. For each P1 and P2 finding, it runs
a small probe in the session scratchpad. It never changes your project. A
typical finding:

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

```
critique labs/proj1, and compare it with ~/work/my-churn-design.md
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

The new `[ref]` items join the open questions in priority order. If a
`[ref]` P1 item contradicts a decision that you made, the skill asks if
you want to reopen that decision.

The skill uses a reference design only when you give one. It never
searches for one.

### 6. Stop early in Normal mode

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
critique this ML system design interview answer, brief
```

There is no project folder, so the skill asks where to save the critique.
The questions in part 4 are the follow-up questions that an interviewer
would ask.

### 9. After the critique

- The skill offers an ADR for each decision that is difficult to reverse.
- If the write-up came from the `ml-*` skills, it offers to send each
  accepted fix to the skill that owns it. Example: a leakage fix goes to
  `ml-modeling-features`. Then the later steps run again.

## Where files go

```
labs/proj1/                 (the parent is labs/ unless you name another)
  critique/2026-10-08-both.md
  critique/2026-10-09-modeling.md
```

- The file name ends in the lens: `system`, `modeling`, or `both`.
- The critique never edits your write-up.
- With no project folder, the file goes in `critique/` in the folder of
  the write-up. For pasted text, the skill asks where to write it.
- Nothing goes in `notes/`. That folder is only for your own content.

## Tips

- For a fair review, keep the default fresh view. Add your own design
  later if you want a comparison.
- Use Brief mode first. Then use Normal mode on the lens that found the
  most P1 items.
- A skill problem found during a run goes to the shared
  `.agents/skills/personal/SKILL-IMPROVEMENTS.md`. The skill does not
  change itself during the run.
