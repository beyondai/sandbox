## 2026-09-20 — grilling (via ml-system-design-prd wrapper)
- **Source**: user-requested
- **Status**: proposed
- **Finding**: The user prefers to answer grilling-round questions through a labeled notes file (e.g. `notes/riot-practice-churn-2.md`, with their own section headers like `#to-prd`) referenced via `@path`, rather than typing every answer in chat — the file doubles as a durable log of inputs and changes. Inputs are deliberately mixed: long-form answers go in the notes file, short answers come through chat; the point is one long-lived doc per session for the long-form parts, not a file per round. The grilling skill has no convention for reading a referenced note file's user-defined sections as the answer to the current round, nor a read-cursor so a later reference to the same file is treated as an incremental append rather than reprocessing the whole file.
- **Suggested change**: When a round answer is a reference to a notes file, read it, match content to open questions via the user's own section labels (no fixed schema), and track how much has already been consumed so a later reference only surfaces new content. Since `grilling` lives in the vendored mattpocock pack, put this in the personal wrapper (`ml-system-design-prd/SKILL.md`) rather than editing the pack.
- (Restored 2026-09-20: this entry was accidentally overwritten by a later full-file write earlier the same day.)

## 2026-09-20 — ml-system-design-high-level
- **Source**: agent-found bug
- **Status**: adopted (2026-09-20)
- **Finding**: `ml-system-design-high-level/SKILL.md` has no "Write the file" section — unlike `ml-system-design-deep-dive/SKILL.md`, which explicitly says to write to `<project-folder>/design/deep-dive.md`. The parent `ml-system-design/SKILL.md` doesn't fill the gap either (it only says artifacts live under the project folder generally). The one existing precedent in this repo, `labs/ml-ecommerce-search-1/adr/0001-ecommerce-search-hybrid-architecture.md`, worked around the gap by folding the entire Architecture+Phasing content into a single ADR — which then reads like a de facto "project ADR," and nearly led to a second confusion (below) about ADRs being a consolidated project log rather than one-per-decision.
- **Suggested change**: Add a "Write the file" section to `ml-system-design-high-level/SKILL.md` pointing at `<project-folder>/design/high-level.md` (parallel to deep-dive's own file), so the section has an unambiguous home and stops getting folded into ADRs by default.

Applied to `.agents/skills/personal/ml-system-design-high-level/SKILL.md` (new "Write the file" section) and `docs/ML-SKILLS-GUIDE.md` (diagram, command table, project-folder tree).

## 2026-09-20 — ml-system-design / domain-modeling (ADR convention)
- **Source**: user-requested (surfaced when the user asked to "update a global ADR which includes all key decisions for this project")
- **Status**: adopted (2026-09-20)
- **Finding**: `ml-system-design/SKILL.md` points to `domain-modeling`'s ADR format for numbering/when-to-write rules, and that format (`ADR-FORMAT.md`) is unambiguous about one-decision-per-file, sequentially numbered. But because the only existing example in this repo (`ml-ecommerce-search-1`'s single ADR) happens to contain a whole project's worth of architecture+phasing content (see the finding above), it visually reads as "the project's consolidated decision doc," which is exactly the wrong pattern to imitate. The user asked to deviate into a single consolidated ADR before catching it themselves once the documented convention was surfaced back to them.
- **Suggested change**: Once the `ml-system-design-high-level` gap above is fixed (so its content stops landing in an ADR by default), the confusion mostly resolves itself. As a belt-and-suspenders fix, `ml-system-design/SKILL.md`'s ADR-location note could add one explicit sentence: "ADRs stay one-per-decision even as a project accumulates several — never a single running project-decisions log" — cheap to add, directly forecloses the failure mode observed here.

Applied to `.agents/skills/personal/ml-system-design/SKILL.md` (sentence appended to the ADR-location paragraph).

## 2026-09-20 — ml-modeling (router): fork point after high-level, not deep-dive
- **Source**: user-requested (user adopted (2026-09-20) it; agent analysis agreed)
- **Status**: adopted (2026-09-20)
- **Finding**: `ml-modeling-*` hard-requires `design/deep-dive.md`, but this session showed the paper deep-dive is a weak gate: (a) writing an honest one required ad-hoc data profiling, which is `ml-modeling-data`'s job done inside a design skill; (b) the decisive design change (revival horizon 28 -> 14 days, which moved revival class balance from ~4-5% to ~2.6-3.7%) came from `design/high-level.md`, forcing a deep-dive rewrite; (c) monkey-mode produced a correct, properly-labeled baseline (PR-AUC 0.477) from grounding equivalent to PRD + ML framing, with no deep-dive at all. The deep-dive's four sections are a paper prediction of the four `ml-modeling-*` outputs, and the hash-and-ask drift machinery exists mainly to police that duplication.
- **Suggested change**: Relax the gate. Minimum grounding = `prd/` + `design/high-level.md`; `design/deep-dive.md` becomes optional, read as prior hypotheses when present. Document two paths: **hands-on** (PRD -> high-level -> `ml-modeling-*`, modeling artifacts are the deep dive, optional back-fill of `design/deep-dive.md` from evidence at the end) and **design** (PRD -> high-level -> deep-dive -> delivery -> post-delivery on paper, may still fork to `ml-modeling` from deep-dive as today). `spec/<topic>.md` pins one hash per design doc present (prd, high-level, deep-dive-if-any) and the "changed?" check covers each. Training-setup decisions get an execution-side home: cutoffs/backtest split/population in `ml-modeling-data`, loss/imbalance handling in `ml-modeling-train`. Record as a new ADR in `.agents/skills/personal/adr/` superseding the fork-point part of 0001; update `docs/ML-SKILLS-GUIDE.md`'s path tables.

Applied in simplified form (deep-dive and ml-modeling are either/or alternatives after high-level, both feeding delivery; no optional deep-dive read, no back-fill): `.agents/skills/personal/ml-modeling/SKILL.md` (gate, grounding table, spec hashes, drift check), `ml-system-design/SKILL.md`, `ml-system-design-deep-dive/SKILL.md`, `ml-system-design-delivery/SKILL.md`, the five step skills + `ml-modeling-autoresearch`, `ml-system-design-monkey-mode`, `adr/0006-fork-after-high-level.md` (new), status note in `adr/0001`, `docs/ML-SKILLS-GUIDE.md`.

## 2026-09-20 — ml-system-design-high-level: ML framing must be fork-grade
- **Source**: agent-found better design (follows from the proposal above)
- **Status**: adopted (2026-09-20)
- **Finding**: The ML-framing item asks for "one precise sentence." If high-level becomes the modeling fork's grounding, that is not enough to construct labels and populations. This project's `design/high-level.md` happened to include target, horizon, and population because of how it was written, not because the skill required them.
- **Suggested change**: Require the ML framing to name, per model: prediction target, label definition and horizon, scoring population (who gets a score and when), and unit of prediction. Complements the already-logged missing "Write the file -> design/high-level.md" section.

Applied to `.agents/skills/personal/ml-system-design-high-level/SKILL.md` (ML framing bullet, Architecture names sources, Phasing names model class, Done-when, fork-point note).

## 2026-09-20 — ml-modeling-data: assumes a target column already exists
- **Source**: agent-found bug
- **Status**: adopted (2026-09-20)
- **Finding**: The Profile section (and `01-data.json`'s `target.column`) assumes a flat dataset with a label column. For this project no such table exists: the labeled tables must be constructed from `activity.csv` with cutoffs and horizons (features strictly `day < c`, labels in `[c, c+H)`, campaign-treated players excluded at the test cutoff). No `ml-modeling-*` step owns that construction; it currently lives only as prose in the deep-dive's Data/Training sections. Handled locally for this project via `modeling/build_dataset.py`.
- **Suggested change**: Add a dataset/label-build step - either inside `ml-modeling-data` (before profiling) or as a `00-build-dataset` step - that reads the label definition, horizons, cutoffs, and population rules from the design docs, writes the labeled tables plus the build script under `modeling/`, and asserts the resulting class balance is not degenerate (the look-ahead-leak check that caught a real bug in this session).

Applied as a `dataset` block in `01-data.json` (one model per project folder, no separate manifest) plus a "Build or register the labeled table" section: `.agents/skills/personal/ml-modeling-data/SKILL.md`, `ml-modeling-features/SKILL.md`, `ml-modeling-train/SKILL.md`, `ml-modeling-multiagent/SKILL.md`, `ml-modeling-evaluate/SKILL.md`, `ml-modeling/SKILL.md`, `docs/ML-SKILLS-GUIDE.md`.

## 2026-09-20 — ml-modeling-data (dashboard): multi-task profile view
- **Source**: agent-found better design
- **Status**: proposed
- **Finding**: `01-data.json` and `assets/dashboard_app.py` are one-table/one-target by design, and the adopted `dataset` contract keeps that (one model per project folder). If two models ever need to live in one folder again, the dashboard has no way to show both profiles.
- **Suggested change**: Only if multi-model folders come back: optional `tasks: {<name>: {...profile...}}` in `01-data.json` and a task selector in `assets/dashboard_app.py`, legacy single-object shape still valid. Deferred on purpose.

## 2026-09-20 — ml-system-design-* sections and ml-modeling-* steps: project-folder resolution
- **Source**: agent-found better design
- **Status**: proposed
- **Finding**: The section skills (`ml-system-design-definition` .. `-post-delivery`) and step skills (`ml-modeling-data` .. `-evaluate`) never say how they decide which `labs/ml-*` folder they are working in; they rely on conversation context. In a fresh session with several practice folders, that is a guess. `ml-system-design-prd` and `ml-system-design-monkey-mode` do have a rule (check for existing `ml-<topic-slug>-*`, ask if several).
- **Suggested change**: One shared rule in the two routers, referenced by every section/step skill: use the folder named in the request; else the folder whose files the conversation has been reading or writing; else, if exactly one `labs/ml-*` exists, that one; otherwise ask. Never create a folder from a step skill - that is `ml-system-design-prd`'s job.
