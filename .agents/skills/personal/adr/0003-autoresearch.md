# Autoresearch: candidate pattern, plateau-based criteria, hard write boundary

**Status: partially superseded by `0005-autoresearch-self-contained-looping.md`.** This ADR's "one round per invocation, delegated recurrence" decision (originally recorded just below) was reversed after real usage showed `/loop`'s interval semantics don't mean what they sound like ("every N minutes," not "for N minutes") and its 7-day auto-expiry was irrelevant noise. Recurrence is now self-contained inside the skill — see `0005` for that decision and why. The other decisions recorded here (candidate-per-round pattern reuse, plateau-based stopping *criteria*, the hard write boundary) are unaffected and still stand.

`ml-modeling-autoresearch` runs after `modeling/04-evaluate.json` exists, dispatching parallel candidates that each try one change to the current best model, keeping the winner if it beats the running best. Adapted from `karpathy/autoresearch`'s philosophy (fixed time budget per experiment, one file as the edit target, keep-or-discard against a running best, a human-editable `program.md` steering the search) rather than copied — that repo is a single fixed GPU training loop; this family already has a parallel multi-candidate pattern (`ml-modeling-multiagent`) and an experiment-logging tool (`experiment_tracker.py`), both reused directly.

## Decisions

**(Superseded — see Status above) One invocation runs exactly one round, never loops internally.** Recurring execution ("keep improving while I do other things") was originally delegated to Claude Code's own `/loop` skill rather than built custom inside this skill.

**Candidates per round reuse `ml-modeling-multiagent`'s pattern, not karpathy's strictly single-threaded one.** The user's own framing was "auto agents" (plural). Each candidate still tries exactly one focused hypothesis, one file, keeping karpathy's "reviewable diff" principle at the level of a single candidate even though multiple candidates run per round. No worktrees needed, for the same reason already established for `ml-modeling-multiagent`: candidates don't touch each other's code, only their own `rounds/round-NNNN/candidate-<id>/` output path.

**Stopping criteria are plateau-based (a streak of non-improving rounds vs. `patience`), not a guessed time or round-count budget — this part is unaffected by the Status note above.** Explicitly discussed with the user: round duration scales with model complexity and data size, so a fixed time/count budget means something different per project and doesn't answer the real question ("has this stopped finding anything"). A generous `round_ceiling` (default 50) exists only as a safety backstop under the plateau signal, not as the primary stopping mechanism. (Superseded: *how* the session actually stops on hitting these — originally "the skill cannot unsubscribe `/loop`, so it can only recommend" — is rewritten in `0005`, since the skill now owns its own recurrence and can act on this directly.)

**Hard write boundary: `modeling/autoresearch/` plus `04-evaluate.md`/`.json` only, never `prd/`, `adr/`, `design/`, or `spec/`.** Confirmed explicitly by the user as a non-negotiable constraint, not just scope hygiene — those are the human's design-decision record, and an unattended, repeatedly-firing loop must never be able to rewrite them regardless of what any round's outcome is.

## Considered Options

Considered having the skill run its own internal multi-round loop (a single invocation trains many candidates over an extended session) rather than delegating to `/loop`. Rejected: Claude Code already has a purpose-built recurring-execution mechanism: reimplementing it inside this skill would duplicate that machinery for no benefit, and would make each individual round less reviewable (no natural checkpoint between rounds for the human to inspect before continuing).

Considered a fixed time or round-count budget as the stopping mechanism (mirroring karpathy's fixed 5-minute-per-experiment design more literally, extended to a fixed total session length). Rejected per the user's own observation: the right bound depends on model complexity and data size, which vary per project — a number picked in advance either stops too early (leaving real improvement on the table for a slow-training complex model) or wastes compute long after diminishing returns set in (for a fast-training simple one). Plateau detection adapts to whatever the actual marginal returns are, without needing that number guessed upfront.

## Consequences

- `program.md` becomes a second place (alongside `design/deep-dive.md`) that steers modeling behavior — a human editing it mid-loop changes what the *next* round does, not the one in flight, since each round reads it fresh at the start.
- Because promotion overwrites `04-evaluate.md`/`.json`, the dashboard's Final Results tab will show whichever model is currently best, not necessarily the one from the original `ml-modeling-evaluate` run — `round-summary.md` and the `rounds/` history are what preserve the full trail if that distinction matters later.
- If a future need arises for autoresearch to also touch `design/deep-dive.md` (e.g. to record a genuinely new feature idea a candidate discovered), that would cross the hard write boundary above and needs a deliberate new decision, not a quiet exception inside the existing skill.
