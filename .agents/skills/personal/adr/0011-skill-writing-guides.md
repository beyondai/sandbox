# Apply 9 skill-writing guides to the ml-* skills

## Context

The user collected 9 guides for skill files
(`notes/skill-improve-guides-20261008.md`): a TOC for long files, freedom
matched to fragility, scripts for fragile steps, tuning for the model,
lean `SKILL.md`, references one level deep, progress checklists,
self-validation, and declared dependencies. An audit of the 18 `ml-*` and
`ml-critique*` skills found gaps for 8 of the 9 guides.

The user set the order: prune and rewrite first, then add a Check step to
each skill, then add TOCs.

## Decision

```
1 Prune + rewrite  ->  2 Check step + scripts  ->  3 TOCs
```

1. **Prune and rewrite.** Concise plain English: imperative steps, lists,
   one term for one concept, and a one-line reason for each rule that is
   not obvious. Long history goes to ADRs. Strict STE is for outputs only:
   it removes the reasons that a strong model needs for edge cases (user
   decision after the first pass). No em dashes. "Skill improvement log" lives
   only in `ml-system-design/SKILL.md`. `SKILL.md` words: 18,678 ->
   16,343 (-13%, after the new Check steps are added).
2. **Check step.** One procedure, "Check the output" in
   `ml-system-design/SKILL.md`: intent questions, `check_doc.py`, fix and
   check again (maximum 2 loops), then reflect and log skill issues. Each
   skill ends with a Check step with 2-4 intent questions for that skill.
   - Autonomous skills (autoresearch, monkey-mode, monkey-mlp) do not ask
     the user. They report skill issues in their summary, because their
     write boundary excludes `SKILL-IMPROVEMENTS.md`.
   - The critique lenses check their critique before they return it. The
     core logs their skill issues.
3. **Scripts (low freedom)** for 3 fragile procedures:
   - `ml-system-design/scripts/check_doc.py`: 80 columns, wide tables, em
     dashes, required sections.
   - `ml-modeling/scripts/spec_hash_check.sh`: the "Design docs changed?"
     check, and `--refresh`.
   - `ml-modeling-data/scripts/launch_dashboard.sh`: free port, `.port`,
     `.pid`, start, reuse, `--stop`. It uses the sandbox venv with
     `uv run --project <root>`, so a project outside the repo also works.
4. **Checklists.** A "Progress" block in the multi-step skills.
5. **Flat links.** The catalogs no longer link the principles doc; they
   state the cost table inline. The lenses link the principles doc. Step
   skills link `ml-system-design/SKILL.md` directly.
6. **Dependencies.** "Bundled tools" in `ml-modeling` lists each script
   with its requirement. The dashboard section names its packages and the
   `uv add` command.
7. **TOCs.** A "Contents" line under the title of each file over 100
   lines.

## Independent test round (2026-10-08)

3 independent agents tested the rewrite (static audit with script edge
cases, the modeling chain end to end, the design chain plus a rule-loss
audit). Fixes made from their findings:
- Scripts: `launch_dashboard.sh` kills or reuses only its own streamlit
  process; `spec_hash_check.sh` runs git in the project's repository and
  prints full SHAs; `check_doc.py` tracks fence type and length, reports
  an unclosed fence, counts display width, and rejects an empty input.
- Step handoff: features writes `features.py` (`transform`), train saves
  `model.joblib` with its threshold, evaluate loads both and saves
  `test_scores.csv`. Evaluate scores a simple-rule baseline and the noise
  of the lift (paired bootstrap).
- One Quick-POC keyword list; broken pointers and paths fixed; reasons
  and details restored where the audit found them lost.
- Old script issues: `experiment_tracker.py` picks the lowest value as
  best for error and loss metrics; the dashboard colors the verdict from
  `verdict_status` (pass, partial, fail) and colors deltas by metric
  direction.
- 7 skill issues from the cold runs: critique file name `both`, Brief
  overflow to Deferred, the Conclusion repeats the top 3, `--sections`
  checks, Brief may read files, definition names the event to predict
  and a fallback when no playbook fits.

## Not applied

- **A `model:` field in the frontmatter.** In Claude Code it switches the
  model that runs the skill. The target model (Opus 5.5) is recorded in
  `docs/ML-SKILLS-GUIDE.md` instead.
- **Splitting a `SKILL.md`.** All are under 250 lines, far below 500.

## Consequences

- A skill output that fails `check_doc.py` is fixed before the skill is
  done. Older project docs (for example `labs/ml-kaggle-churn-1`) still
  have em dashes. They are records, so they stay as written.
- Skill issues now come from each run, not only from the user.
