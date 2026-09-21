## 2026-09-20 — ml-system-design-prd
- **Source**: user-requested
- **Status**: adopted
- **Finding**: In Quick POC mode, the one-pass draft round bundled all seven
  Definition checklist items into a single grilling round (7 numbered
  questions at once). The user asked instead for POC rounds to be capped at
  6 questions, splitting into more than one round when the checklist has
  more items than that, while still allowing free-form user input at the
  end of a round rather than only per-question confirm/override.
- **Suggested change**: In `ml-system-design-prd/SKILL.md`'s "Quick POC round
  shape" section, cap each POC round at 6 numbered questions. When the
  Definition checklist (or any seeded design tree) has more than 6 open
  items, split the one-pass draft into consecutive rounds of at most 6 each
  instead of one large round. End each round with an explicit invitation for
  free-form input (not just per-item overrides), e.g. "anything else to add
  or change before I move on?" - so the user isn't limited to reacting item
  by item.

## 2026-09-20 - ml-system-design-monkey-mode
- **Source**: agent-found bug
- **Status**: adopted (modified per user)
- **Finding**: The skill's fast defaults assume `pandas`/`scikit-learn` are
  importable, but the system `python3` (3.14, `/usr/local/bin/python3`) has
  neither installed, and no project-local Python environment exists yet at
  the start of a monkey-mode run. The dispatched agent has to discover this
  by trial and error (a bare `import pandas` failure), then locate an
  alternate interpreter or build a venv, before any real work can start.
  This is pure overhead that every monkey-mode run on a fresh machine will
  hit identically.
- **Suggested change (as adopted)**: Add a step to the Process (before step
  3's dispatch): install missing packages into a project-local venv at
  `<project-folder>/monkey-mode/.venv` (`pip install`, `.gitignore` entry
  for `.venv/`) as before, and additionally have the dispatched agent note
  in its report when it had to do this, as a candidate to add to the base
  sandbox environment so future runs on this machine skip the reinstall.
  Applied to `ml-system-design-monkey-mode/SKILL.md`'s Process step 3.

## 2026-09-20 - ml-system-design-monkey-mode (follow-up)
- **Source**: user-requested
- **Status**: adopted
- **Finding**: Raised alongside the venv fix above: the success-bar "look
  one up" web search for a domain benchmark had no time limit, so a
  monkey-mode run could spend an open-ended amount of time searching for a
  citation before getting to the actual baseline.
- **Suggested change**: Time-box the "look one up" benchmark search to 2
  minutes - take the best citation found in that window rather than
  continuing to search for a perfect match. Applied to
  `ml-system-design-monkey-mode/SKILL.md`'s success-bar question.

## 2026-09-20 — ml-modeling
- **Source**: user-requested
- **Status**: adopted
- **Finding**: Invoking `/ml-modeling <topic>` (the full-chain entry point)
  ran all four steps (data, features, train, evaluate) back to back with
  no pause between them. The user expected the same step-by-step,
  checkpointed collaboration already used for `prd/` and
  `design/high-level.md` in this project (review after each step, not one
  long unattended run), even though `/ml-modeling` reads as "run the whole
  chain in order" per its own SKILL.md.
- **Suggested change**: In `ml-modeling/SKILL.md`, make `/ml-modeling
  <topic>` the entry point for the step-by-step path rather than an
  auto-chain-to-completion command: invoke step 1, report its result, and
  stop for user confirmation before invoking step 2, and so on through
  step 4 - mirroring how `ml-system-design-prd` and
  `ml-system-design-high-level` already checkpoint with the user. Keep a
  separate explicit way to request the old uninterrupted behavior (e.g. a
  keyword like "full chain" or "run all four steps") for when the user
  wants one continuous pass.

## 2026-09-20 - ml-modeling-data
- **Source**: user-requested
- **Status**: adopted
- **Finding**: The Streamlit dashboard launched by this skill (e.g.
  `dashboard/app.py` on a port recorded in `dashboard/.port`) is left
  running as a background process after the work session ends. Found two
  stray dashboards running at once from unrelated projects (one from an
  archived project, running since the prior weekend), each holding a port
  open indefinitely with nothing to stop them.
- **Suggested change (as adopted)**: Added a global `Stop` hook
  (`~/dev/dotfiles/home/.claude/hooks/kill-project-dashboards.sh`, wired in
  `~/dev/dotfiles/home/.claude/settings.json`) that on session end scans the
  session's working-directory tree for `dashboard/.pid` or `dashboard/.port`
  files and kills whatever is bound to that PID/port - verified against both
  a direct process and the real `uv run streamlit run ...` two-process case
  (killing either the wrapper or the actual port-holder correctly tears down
  both). Also updated `ml-modeling-data/SKILL.md`'s launch step to write
  `dashboard/.pid` (`echo $! > dashboard/.pid`) alongside `dashboard/.port`
  for exact targeting; the hook still falls back to a port lookup for
  projects that predate the `.pid` file. Killed the two stray dashboards
  found during this session as a one-off cleanup.
