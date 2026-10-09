---
name: ml-system-design
description: >-
  Use when writing, structuring, or reviewing a full ML system design document,
  RFC, or ML system design interview answer for a machine learning product or
  feature (ranking, recommendation, search, fraud/risk, forecasting, NLP/LLM
  systems, etc). Entry point for the whole doc; for one section only, trigger
  that section's own skill directly instead. Trigger on "ML system design,"
  "design doc for a model," "ML RFC," or ML system design interview prep.
---

# ML System Design

Contents: Steps | Project folder | Output docs | Check the output | Hand edits
between steps | Regular and Quick-POC mode | The fork: paper or hands-on |
Related skills and docs | Skill improvement log

A full design doc has 5 sections. Each section is its own skill:

1. `ml-system-design-definition`: problem, requirements, baseline,
   metrics, team.
2. `ml-system-design-high-level`: ML framing, architecture, phasing.
3. `ml-system-design-deep-dive`: data, features, models, training,
   serving.
4. `ml-system-design-delivery`: execution, deployment, evaluation,
   monitoring, fallback.
5. `ml-system-design-post-delivery`: analysis, explainability, iteration,
   democratize.

```
prd (= definition) -> high-level -> [ deep-dive (paper)          ] -> delivery -> post-delivery
                                    [ ml-modeling-* (hands-on)   ]
```

## Steps

Progress (copy into your reply, tick each line):

```
[ ] 1 Offer monkey-mode and the PRD (new project only)
[ ] 2 Definition, or the PRD
[ ] 3 High-level
[ ] 4 Deep dive, or the ml-modeling chain
[ ] 5 Delivery
[ ] 6 Post-delivery
[ ] 7 Check each file (see "Check the output")
```

1. **New project.** Before any section skill, ask 2 questions in one
   message. The recommended answer to each is yes:
   - Run `/ml-system-design-monkey-mode <topic>` in the background as a
     baseline?
   - Scope with `/ml-system-design-prd <topic>` first?

   The user types these commands. Skip the questions only when the user
   names one section.
2. **Order.** Run the section skills in order. If
   `<project-folder>/prd/<topic>.md` exists, it is the Definition: start at
   `ml-system-design-high-level`. For one section, run that skill only.
3. **Interview prep.** Go through the 5 sections in order. Use each skill's
   bullets as the interviewer's follow-up questions.
4. **Depth.** Scale the depth to the system size. Never skip these 3
   items: out-of-scope and the baseline (definition), and the fallback
   (delivery). Docs skip them most often, and reviews flag them most.
5. **Monkey-mode in the background.** Tell the agent that the project
   folder is shared and in progress, also for a new project. It creates
   only its own `monkey-mode/` subfolder. (A background agent told that the
   folder "does not exist yet" once reset the folder and deleted a PRD.)
6. **ADRs.** Write each architectural decision as one ADR in
   `<project-folder>/adr/`. Use the numbering and the rules of the
   `domain-modeling` skill's ADR format. One ADR for each decision. A
   design section goes in `design/`, never in an ADR.

## Project folder

This section is the single source of truth for where all `ml-*` and
`ml-critique*` skills save files.

```
<parent>/                  default: labs/ (the user can name another)
  <project>/               for example: proj1/
    prd/  design/  adr/  spec/  modeling/  dashboard/
    critique/  research/  monkey-mode/  monkey-mlp/
```

- **Project name.** Use the name that the user gives (for example
  `proj1`), as a lowercase slug. If the user gives only a topic, propose
  `ml-<topic-slug>` and confirm it. Add `-<n>` only for a new attempt at a
  project that already exists: ask "continue the existing project, or
  start a new attempt?" first.
- **Parent folder.** The default is `labs/`. The user can name another
  parent in the request (for example "put proj1 in ~/work/designs"). Later
  requests name the project by its path.
- **Subfolders.** A skill creates its subfolder the first time that it
  writes there. Every other file for the project (research, test records)
  goes in a subfolder of the project folder. `notes/` holds only what the
  user typed or pasted: read it, and create no files there.

### Which project folder

Use the first rule that applies:
1. The project named in the request. A path is used as given. A name with
   no path is looked up under `labs/`.
2. The project folder that this conversation already read or wrote.
3. If exactly one project folder exists under `labs/`, that one. A
   project folder is a direct child of the parent that has at least one of
   the subfolders above.
4. Ask the user.

Only `/ml-system-design-prd` and the monkey tracks create a project
folder. Section and step skills never create one.

## Output docs

Every file under the project folder follows these rules:
- Wrap prose at 80 columns. Use hard line breaks in paragraphs and list
  items. Indent continuation lines under their bullet. Fenced code blocks
  are the exception.
- If a table row is longer than 80 columns, write a list of headed
  paragraphs instead. The reader uses a terminal.
- Write in about 80% ASD-STE100: short sentences (20 words or fewer for
  instructions, 25 for descriptions), one instruction in each sentence,
  active voice, one word for one meaning, lists over long paragraphs. Keep
  technical names as they are.
- Add a fenced ASCII diagram next to the text when structure, data flow,
  sequence, or a timeline is easier to see. The text stays complete
  without the diagram.
- No em dashes.

## Check the output

Every `ml-*` and `ml-critique*` skill ends with this step. The skill's own
"Check" step gives its intent questions.

1. **Intent.** Read the output again. Compare it with the skill's purpose,
   the user's request, and the skill's intent questions. Answer each
   question with yes or no and a line reference, in your reply.
2. **Format.** Run this on each `.md` file that the skill wrote. If the
   skill names required headings, add `--sections "<A>,<B>"`. It prints
   `OK` or `file:line: reason`.

   ```
   python3 .agents/skills/personal/ml-system-design/scripts/check_doc.py <files>
   ```
3. **Fix.** For each "no" and each failure, fix the output. Then do steps 1
   and 2 again. Stop after 2 loops, and tell the user what is still open.
4. **Reflect.** Did a gap or an error in the skill cause a problem? Did the
   user correct how the skill works? If yes, add an entry to the skill
   improvement log (below).

## Hand edits between steps

The user can edit any file in the project folder between steps. When a
file changed:
1. Read it again.
2. Run again each downstream step whose file uses the changed content.
   Update those files in place. The downstream order: `prd/` ->
   `design/high-level.md` -> `design/deep-dive.md` or `spec/` + `modeling/`
   -> delivery -> post-delivery.
3. Add one line to a `## Change log` heading at the end of each changed
   file: what changed, and why.

On the hands-on route, `spec_hash_check.sh` finds the same edits (see
`../ml-modeling/SKILL.md`, "Design docs changed?").

## Regular and Quick-POC mode

Each section skill has the 2 modes. The keyword in the request selects
the mode. There are no flags.
- Quick POC: "poc", "quick", "mvp", "prototype", "fast", "one hour",
  "1 hour". A
  one-hour MVP, at the same quality. Section skills answer in one pass
  and mark each guess as an assumption. The PRD and the deep dive ask
  their essential questions in batched rounds. This is the one keyword
  list for all `ml-*` skills.
- Regular: "regular", "full", or no keyword. Full rigor. Ask when a fact
  is unknown.

Reason: `../adr/0001-ml-modeling-family-and-continuity.md`.

## The fork: paper or hands-on

After `design/high-level.md`, select one route:
- **Paper:** `ml-system-design-deep-dive` writes `design/deep-dive.md`.
- **Hands-on:** the `ml-modeling` chain (data -> features -> train ->
  evaluate -> serve) writes `spec/<topic>.md` and `modeling/01`-`05`. It
  does not read `design/deep-dive.md`.

Both routes answer the same 5 items, serving included, so delivery gets
the same facts on either route (`../adr/0013-serving-on-both-routes.md`).
Delivery uses the file that exists. If both exist, it uses the newer one
(with modeling, the real numbers from `04-evaluate.md` and
`05-serve.md`). When execution
contradicts the framing, send the change back to `design/high-level.md`.
Reason:
`../adr/0006-fork-after-high-level.md`.

## Related skills and docs

- `../ml-design-principles.md`: the principles that each skill applies and
  that `ml-critique` uses. Principle 1: simple by default, complex only
  with evidence.
- `ml-critique`: judges the quality of a finished write-up, and settles
  each finding with the user. It writes `<project-folder>/critique/`. A
  section skill's Review mode checks only coverage.
- `ml-system-design-monkey-mode`: an autonomous fast baseline. It shares
  only the project folder. It does not read `prd/` or `design/`, and it
  does not write `modeling/`. The user runs it by hand.

## Skill improvement log

This section is the single source of truth for all `ml-*` and
`ml-critique*` skills.

The log is about the skills, not about a project: each entry changes a
skill that every future project uses. Project decisions stay in the
project's own docs.

Log an entry when one of these occurs, in a skill run or between runs
(discussion, follow-up work):
1. **Agent-found:** a bug in the skill's instructions, or a better method
   than the one written.
2. **User-requested:** the user asks to change how the skill works (not a
   one-time request for this project). Log it at once.

Add the entry to the one shared log, `.agents/skills/personal/SKILL-IMPROVEMENTS.md`.
Do not edit the `SKILL.md` during the run, unless the user asks: a skill
file serves every future project, so a drive-by edit from one run changes
behavior everywhere. The log gives a batch to review.

```markdown
## <date> - <skill-name>
- **Project**: <project folder where it was found>
- **Source**: agent-found bug | agent-found better design | user-requested
- **Status**: proposed
- **Finding**: <what is wrong or what can be better>
- **Suggested change**: <the edit, ready to apply>
```

**Review.** At the end of each run, after the task, look for entries with
`Status: proposed`. If there are any, say so and offer to review them. For
each entry, ask: adopt or decline? Apply an adopted entry to
`.agents/skills/personal/<skill>/SKILL.md`. Then set `Status` to `adopted`
or `declined`, and follow "Skill and docs changes" in the sandbox
`CLAUDE.md`. Never delete an entry.

**Session end.** At the end of every session that used an `ml-*` or
`ml-critique*` skill, before the final summary: reflect on the whole
session (skill runs, discussion, user corrections), log each new skill
issue, then offer the review above. The sandbox `CLAUDE.md` has the same
rule, so it applies even when no skill run is active.

Reasons: `../adr/0004-skill-improvement-log.md`,
`../adr/0016-shared-log-and-session-end-reflection.md`. Older entries stay
in `labs/<project>/SKILL-IMPROVEMENTS.md` as history.
