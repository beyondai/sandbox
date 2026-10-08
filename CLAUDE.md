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
