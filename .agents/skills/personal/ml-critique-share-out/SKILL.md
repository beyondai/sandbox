---
name: ml-critique-share-out
description: >-
  Turn a final ML critique into a share-out plan: what to discuss, in which
  order, in a fixed time, for a given audience (an interview, a design
  review, a launch review). Takes a critique file and a share-out context
  (purpose, audience, format, time limit, required topics). Use when the
  user must discuss or share a critique in a meeting or an interview.
---

# ML Critique Share-out

Contents: Purpose | Steps | Talking point | Done when

## Purpose

- **Problem.** A full critique has 30 to 60 items. A share-out has a
  fixed time, an audience, and required topics. The person who shares
  must know what to say first, what to cut, and how to answer follow-up
  questions.
- **Use** this skill to make a share-out plan from one final critique.
- **Output.** `critique/<date>-share-out.md`: a timeline, the talking
  points, the questions to ask, a backup list, a cut list, and how to
  deliver.
- **Input.** One critique file (from `ml-critique` or
  `ml-critique-merge`). If the user gives several, run `ml-critique-merge`
  first. Reason: one owner for the merge rules.
- Uses the priority and the sort key of `../ml-critique/SKILL.md`
  ("Priority").
- How to deliver, by context type:
  [references/delivery.md](references/delivery.md).
- Rationale: `../adr/0020-critique-merge-share-out-one-mode.md`.

```
 final critique + share-out context
      --> 1 Select (limit, topics, audience)
      --> 2 Propose (plan that fits the limit)
      --> 3 Discuss (rounds, until "write")
      --> 4 Write (critique/<date>-share-out.md)
      --> 5 Check
```

## Steps

Progress (copy into your reply, tick each line):

```
[ ] 1 Select: critique file, share-out context, share-out limit (ask and wait)
[ ] 2 Propose: plan that fits the limit
[ ] 3 Discuss: rounds until the user says to write
[ ] 4 Write: critique/<date>-share-out.md
[ ] 5 Check
```

### 1. Select

1. Find the critique file. If there are several, run `ml-critique-merge`
   first and use its final critique.
2. Ask for the share-out context (path or text), unless the user gave
   one. Examples: an interview brief, a meeting invite, "15 minutes in the
   team design review".
3. Read from the context:
   - **Share-out limit:** the discussion time and the format (screen
     share, sketches, slides, written).
   - **Required topics:** for example "done well, change, missing,
     questions".
   - **Audience and setting:** interviewer, team, decision maker; working
     session, review, go/no-go.

   Ask only for what the context does not give. Wait for the answer.
4. Select the context type in `references/delivery.md`. Tell the user
   the type in one line.

### 2. Propose

1. Budget the time. Keep about 20% free for follow-up questions. Reason:
   in a discussion the other side asks, and a full plan has no room.
2. Select the talking points in sort-key order. Each required topic gets
   at least one point. A P1 is never cut while a P2 or P3 is in.
3. Make each talking point (see "Talking point").
4. Put the rest in Backup (if time is left) or in the Cut list (with the
   reason: time, low priority, rejected in the critique).
5. Show in chat: the timeline, the talking points (short form), the
   questions to ask, Backup, and the Cut list. Then the delivery notes
   for the context type.

### 3. Discuss

- Run rounds with the user. The user can keep, drop, move, reword, or add
  a point, change the time per block, or change the context.
- No round limit. Write nothing until the user says to write. Reason: the
  user decides what they will say.
- Tag each new point that the user adds `[user]`. Keep the `[user]` and
  `[ref]` tags of the critique.
- If the user wants to change a finding (not only its order or words),
  say that the critique file does not change. Offer to note it in the
  share-out file as "changed since the critique".

### 4. Write

1. Write `<project-folder>/critique/<YYYY-MM-DD>-share-out.md`, in the
   folder of the critique. If it exists, add `-v<N>`. Never write in
   `notes/`. Use "Output docs" in `../ml-system-design/SKILL.md`.
2. Do not edit the critique or the write-up.
3. Sections, in this order: Summary, Context, Timeline, Talking points,
   Questions to ask, Backup, Cut list, How to deliver.
   - **Summary:** the critique file, the context source, the limit, and
     the top 3 messages.
   - **Context:** the limit, the format, the required topics, the
     audience, and the context type.
   - **Timeline:** an ASCII timeline with a block for each topic and the
     free time.
   - **Talking points:** in the order of the timeline.
   - **Questions to ask:** the questions for the other side, each with
     why it matters.
   - **How to deliver:** the notes from `references/delivery.md` for this
     context type, fitted to this share-out.
4. In the Check, run `check_doc.py` with:

   ```
   --sections "Summary,Context,Timeline,Talking points,Questions to ask,Backup,Cut list,How to deliver"
   ```

### 5. Check

Do "Check the output" in `../ml-system-design/SKILL.md`. Intent questions:
1. Does the timeline fit the share-out limit, with free time for
   follow-up questions?
2. Does each required topic of the context have at least one point?
3. Does each talking point have the claim, the evidence, and the
   alternative? Does each P1 point have its follow-up answers?
4. Does each Cut list item have a reason? Is no P1 cut while a P2 or P3
   is in?
5. Are the `[user]` and `[ref]` tags kept? Are the critique and the
   write-up unchanged?

## Talking point

Each talking point has:
- **Claim:** one sentence. It is what to say first.
- **Evidence:** the quote or the calculation from the critique.
- **Alternative:** the fix, in 1-3 lines.
- **Sketch:** an ASCII sketch when the structure or the flow helps (for
  a "be ready to sketch" context, at least for the top 3).
- **Follow-ups:** the 2-3 likely follow-up questions, each with a short
  answer from the critique.
- **Time:** the minutes for the point.

## Done when

1. The plan fits the share-out limit and covers each required topic.
2. The user said to write, and the file is written.
3. The Check passed (5 yes answers, `check_doc.py` prints `OK`), or the
   open items are reported.
4. The user confirms.
