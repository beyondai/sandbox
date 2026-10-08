# One folder per project, with a parent that the user can change

## Context

The skills used the fixed path `labs/ml-<topic-slug>-<n>/`. 3 problems:

- The user names projects (for example `proj1`). The skills made a name
  from the topic instead.
- The parent `labs/` was fixed. The user wants to put a project somewhere
  else.
- Some generated files went outside the project folder. The vendored
  `research` skill wrote to `notes/`, which holds only user-written
  content.

## Decision

```
<parent>/                  default: labs/
  <project>/               the user's name, for example proj1/
    prd/  design/  adr/  spec/  modeling/  dashboard/
    critique/  research/  monkey-mode/  monkey-mlp/
```

1. All files generated for a project go in `<parent>/<project>/`, in a
   subfolder.
2. The project name is the name the user gives, as a slug. With only a
   topic, the skill proposes `ml-<topic-slug>` and confirms it. `-<n>` is
   only for a new attempt at an existing project.
3. The parent is `labs/` by default. The user can name another parent in
   the request.
4. The single source of truth is `ml-system-design/SKILL.md`, "Project
   folder". All other skills point to it. The sandbox `CLAUDE.md` states
   the rule for skills that cannot be edited (vendored skills).
5. `notes/` holds only content that the user typed or pasted.

## Consequences

- Existing `labs/ml-*-<n>/` folders still work. They are project folders
  with older names.
- A project with a custom parent is found by its path in later requests.
  The discovery fallback ("exactly one project folder") looks only in
  `labs/`.
- ADRs 0001 to 0008 still show the old `labs/ml-<topic>-<n>/` paths. They
  are historical records, so they stay as written.
