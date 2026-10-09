# ML Critique Guide

How to use the `ml-critique` skills, with examples. Skill files:
`.agents/skills/personal/ml-critique*/`. Rationale: `adr/0009`. Principles
that the review applies: `.agents/skills/personal/ml-design-principles.md`.

## What the skills do

You give a finished ML write-up. The skills review it as a chief ML
architect, most important problems first. Then they work with you until
each problem has a decision, and they record the decisions and the
trade-offs.

| Skill | Use it for |
|---|---|
| `ml-critique` | The entry point. It selects the mode and the lens, and runs the whole procedure. |
| `ml-critique-system` | The system lens: goal, metrics, framing, labels, data, architecture, phasing, delivery. |
| `ml-critique-modeling` | The modeling lens: baseline, dataset, split, leakage, features, model, evaluation. |

Use `ml-critique` in most cases. It calls the correct lens. The lens skills
also work alone when you want only one view.

When to use a different skill:
- To **write** a design: `ml-system-design` or `ml-modeling`.
- To check that each section is **present**: the section skill's Review
  mode.
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
```

1. **Select.** The skill selects the mode from your words, the lens from
   the content, and the problem type (churn, recommendation, fraud, and
   others). It asks one question: do you want to compare with a reference
   design of your own? The default is "no", for a fresh view.
2. **Critique.** Each lens runs in a new subagent, so it reads the text and
   not the author's intent. It returns 4 parts:
   1. **Done well**: what to keep.
   2. **Change or fix**: each item with priority, evidence, effect, and an
      alternative.
   3. **Missing**: each item with the standard method.
   4. **Questions**: clarifications and the questions that the designer did
      not ask, each with an expected answer.
3. **Converge.** The skill asks numbered questions with a recommended
   answer, P1 first. You answer each one: **accept**, **modify**,
   **reject** (give a reason), or **defer** (give an owner and the
   condition that unblocks it).
4. **Document.** The skill writes one file with the 4 parts, the decisions
   and trade-offs, the deferred items, and a verdict: `ready`, `ready with
   changes`, or `needs rework`.

## Priority

| Priority | Meaning | Examples |
|---|---|---|
| P1 | Vague or wrong at the core | The problem is not clear. Wrong label, metric, or model family. No real baseline. Leakage. A split unlike production. |
| P2 | A large gain | Better performance, lower cost, a stronger baseline, a simpler design with the same result |
| P3 | A small gain | Polish, small gaps |

Upstream problems come first: an error in the goal or the label makes all
later work wrong. The summary starts with the top 3 changes.

The review applies Principle 1: simple by default, complex only with
evidence. A complex model that wins by less than the noise, or that costs
more than its gain is worth, is a P2 finding.

## Modes

| | Brief | Normal (default) |
|---|---|---|
| Keyword | "brief", "quick", "45 min" | anything else |
| Time | About 45 minutes | A few hours |
| Findings | P1 and P2. Up to 5 for each part. A limit never removes a P1. | All, P1 to P3 |
| Modeling evidence | Code lines and existing output | Command output (probes) |
| Rounds | 2 rounds, 6 questions each | Until all items are resolved |
| Checkpoints | None | After each phase and each round |

In Normal mode, you can say "next step" at any checkpoint. The open items
then go to the Deferred section. Nothing is lost.

## Examples

### 1. A quick review of a whole project

```
/ml-critique brief labs/proj1
```

What happens:
1. The skill says: "Mode: Brief. Lenses: system and modeling. Problem
   type: churn and retention. Do you want to compare with a reference
   design of your own? Default: no, a fresh view." You answer "no".
2. 2 lenses run in parallel. You get the top 3 changes and the 4 parts.
3. Round 1 has the P1 items. Round 2 has the rest. Each question looks
   like this:

   ```
   ❓ Q3 - Scoring population: the code keeps players who already left
   (build_dataset.py:106). Precision@20% = 0.997. Score only players
   active in (90, 120]?

   ➡️ Accept. The current metric measures players who are already gone.
   ```

4. The file `labs/proj1/critique/2026-10-08-both.md` is written.

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

The lens still reviews the write-up without the reference. After that, a
separate reference pass compares the 2 designs. Its items have the tag
`[ref]`. The reference is one more opinion, not the truth: the skill also
says where the write-up is better than your design.

### 5. Add your design in the middle of the discussion

During Converge, say:

```
here is my own design for this: labs/proj1-mine/design/high-level.md
```

The new `[ref]` items join the open questions in priority order. If one of
them is a P1 that contradicts a decision that you already made, the skill
asks if you want to reopen that decision.

The skill uses a reference design only when you give one. It never
searches for one.

### 6. Stop early in Normal mode

At a checkpoint, say:

```
go to the next step
```

Each open item goes to Deferred with the reason "the user went to the next
step". Each one has an owner, an unblock condition, and a risk.

### 7. Answer in a notes file

For long answers, write them in your notes file and point to it:

```
answers are in @notes/proj1.md under #critique
```

The skill reads only the new content, and says which questions it
answered.

### 8. Review a pasted interview answer

Paste the answer, then say:

```
critique this ML system design interview answer, brief
```

There is no project folder, so the skill asks where to save the critique.
The questions in part 4 are the follow-ups that an interviewer would ask.

### 9. After the critique

- The skill offers an ADR for each decision that is difficult to reverse.
- If the write-up came from the `ml-*` skills, it offers to send each
  accepted fix to the skill that owns it. For example, a leakage fix goes
  to `ml-modeling-features`, then the later steps run again.

## Where files go

```
labs/proj1/                 (parent is labs/ unless you name another)
  critique/2026-10-08-both.md
  critique/2026-10-09-modeling.md
```

- The critique never edits your write-up.
- Without a project folder, the file goes in `critique/` in the folder of
  the write-up. For pasted text, the skill asks.
- Nothing goes in `notes/`. That folder is only for your own content.

## Tips

- For a fair review, keep the default fresh view. Add your own design
  later if you want a comparison.
- Use Brief mode first. Then use Normal mode on the lens that found the
  most P1 items.
- A skill problem found during a run is logged in the project's
  `SKILL-IMPROVEMENTS.md`, not fixed during the run.
