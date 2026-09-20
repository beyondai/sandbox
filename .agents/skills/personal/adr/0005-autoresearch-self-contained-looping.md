# Autoresearch: self-contained recurrence, not delegated to /loop

`ml-modeling-autoresearch` (`0003`) originally delegated "keep running" to Claude Code's `/loop` skill, wrapped around a strict one-round-per-invocation design. Live usage exposed two problems with that, both surfaced directly by the user during actual use, not found in review:

1. **`/loop`'s interval means "gap between fires," not "total duration."** `/loop 5m ...` was read as "loop for 5 minutes" but per that skill's own documented parsing rules actually means "fire every 5 minutes, indefinitely." Confirmed against `/loop`'s own SKILL.md, not assumed.
2. **The 7-day auto-expiry is an irrelevant platform detail.** It's a generic `CronCreate` safety limit unrelated to autoresearch's own design, but it surfaced in conversation as if it were part of the stopping story, adding noise to a design that already has its own plateau-based stopping criteria (`0003`).

When the user asked to actually honor "loop for 5 minutes," the working fix needed no scheduling infrastructure at all: running several rounds back-to-back within one continuous execution, tracking wall-clock elapsed time directly, and stopping once the window closed. That was demonstrated live (rounds 3-4 of a real session, ~215 seconds, real promotions: F1 0.6415 → 0.6667) before being written into the skill as its documented behavior.

## Decisions

**Recurrence moved in-house — three explicit modes (one round, until plateau, for a duration), no external scheduling.** All three are one mechanic: run a round, check stop conditions, run another round immediately if none are met, all within the same continuous execution. This directly reverses `0003`'s "delegate to `/loop`" decision.

**A duration, when given, is just one more stop condition alongside plateau and the round ceiling — not a replacement for them.** "For a duration" now also stops early on plateau, rather than burning the rest of a time window once nothing is improving. This wasn't possible under the old design, where duration wasn't a concept the skill had at all.

**Multi-round modes now actually stop themselves**, rather than only recommending a stop. Under the old design the skill had no way to unsubscribe `/loop` from inside a round, so hitting `patience` could only be reported, never acted on. With recurrence brought in-house, "stop" is just "don't run another round" — directly within the skill's own control.

## Considered Options

Considered keeping `/loop` for "until plateau" and "for a duration," and only adding the new mode vocabulary on top (i.e., have the skill's own report tell the user which exact `/loop` invocation to use per mode). Rejected: this doesn't fix the actual problem — `/loop`'s interval still means "gap between fires," so "for a duration" still isn't expressible through it without a second, self-canceling scheduled job working around that gap. The self-contained version needed no such workaround and was already proven working.

Considered building a general-purpose "run until condition" primitive reusable by other skills in this family, rather than something local to autoresearch. Rejected for now: no other skill in the family currently needs multi-round recurrence, and generalizing a mechanic that has had exactly one real use so far risks over-engineering for a need that doesn't yet exist. If a second skill needs this shape, revisit as a shared pattern then, not speculatively now.

## Consequences

- `ml-modeling-autoresearch`'s single invocation can now run for an extended, unattended stretch (up to `round_ceiling` rounds, or the requested duration) without yielding control back to the human between rounds — a real shift from `0003`'s "each round stays bounded and reviewable by design" reasoning. The hard write boundary (`0003`) is what bounds the blast radius of that unattended stretch, not per-round human checkpoints anymore.
- Nothing about how a single round works changed (candidate dispatch, promotion, the path-depth gotcha on promotion, the write boundary) — only how many rounds run per invocation and what decides when to stop asking for more.
- `docs/ML-SKILLS-GUIDE.md` and `ml-modeling/SKILL.md`'s autoresearch sections needed updating in lockstep with this — both described the old `/loop`-wrapped usage as the documented interface.
