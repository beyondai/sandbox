# Skill Improvements

## 2026-09-19 — ml-modeling-autoresearch
- **Source**: user-requested
- **Status**: adopted
- **Finding**: The skill delegated recurring rounds to Claude Code's `/loop` skill. Live use exposed two problems: `/loop`'s interval means "fire every N minutes," not "run for N minutes total" — genuinely surprising, confirmed against `/loop`'s own documented parsing. And its 7-day auto-expiry is an unrelated platform safety limit that surfaced as if it were part of autoresearch's own stopping design, when it isn't.
- **Suggested change**: Replace `/loop`-delegated recurrence with three self-contained modes on the skill itself: one round (default), until plateau, for a duration. All three are one mechanic (run a round, check stop conditions, run another round immediately if none are met) executed entirely within a single invocation — no external scheduling, no interval, no expiry. "For a duration" also stops early on plateau. Already reviewed and approved via full plan-mode review before implementation (not just this log entry) — see `.agents/skills/personal/adr/0005-autoresearch-self-contained-looping.md` for the full design rationale and what was considered and rejected.

Applied directly to `.agents/skills/personal/ml-modeling-autoresearch/SKILL.md`, `.agents/skills/personal/ml-modeling/SKILL.md`, `.agents/skills/personal/ml-modeling-evaluate/SKILL.md`, `.agents/skills/personal/adr/0003-autoresearch.md` (status note), `.agents/skills/personal/adr/0005-autoresearch-self-contained-looping.md` (new), and `docs/ML-SKILLS-GUIDE.md`.
