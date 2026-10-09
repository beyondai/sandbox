# Sandbox instructions

## Where generated files go

- `notes/` holds only content that the user typed or pasted. Do not create
  files in `notes/`. Edit a `notes/` file only when the user asks.
- A file that a skill or an agent creates (designs, research, critiques,
  reports, test records) goes in the project folder that it is for:
  `<parent>/<project>/<subfolder>/`, for example `labs/proj1/research/`.
  The parent is `labs/` unless the user names another. Full rule:
  `.agents/skills/personal/ml-system-design/SKILL.md`, "Project folder".
- If the file is for no project, ask the user where to put it. Use the
  session scratchpad for temporary files.

## Skill and docs changes

Steps are in `docs/SKILL-STYLE-GUIDE.md`, "How to check". Run them before
you say done, and show the output.

- After every skill change, major or not: update each `docs/` file that
  describes the change, run `check_docs.py`, and do the docs checklist
  (steps 3-5). A small change (a keyword, a file name) makes the docs
  wrong as easily as a big one.
- After every edit to `docs/`: run `check_docs.py` and the docs
  checklist (steps 4-5).
- After a major skill change, also run `check_skill_style.py` and the
  skills checklist (steps 1-2). Major = a new skill, a skill rewrite, a
  change to 3 or more skill files, or a new shared reference in
  `.agents/skills/personal/`.
- Record each major skill change in an ADR in
  `.agents/skills/personal/adr/`, and add it to the README index.
