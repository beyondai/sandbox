#!/usr/bin/env python3
"""Check skill files against the mechanical rules in docs/SKILL-STYLE-GUIDE.md.

Usage:
  python3 check_skill_style.py <skills-dir> [<skills-dir> ...]

A skills dir holds skill folders (each with a SKILL.md) and shared .md
references, for example .agents/skills/personal. Checks:
  - SKILL.md frontmatter has `name` equal to the folder, and `description`;
  - SKILL.md is at most 500 lines;
  - a .md file over 100 lines has "Contents" in its first 20 lines;
  - no em dash in a .md file;
  - each SKILL.md has a heading that contains "Check";
  - each relative link, and each backtick path that starts with ../,
    references/, scripts/, or .agents/, resolves;
  - each file in a skill's references/ and scripts/ is named in its
    SKILL.md (links one level deep);
  - each script has a "Requires:" line (declared dependencies).
Skipped: adr/ (historical records), tests/, assets/, and this script's own
folder. The rules that need judgment (freedom level, reasons, plain
English) are a manual checklist in the style guide.

Prints "file:line: reason" for each failure, or "OK (<n> files)".
Exit code 0 when clean, 1 on a failure, 2 on a usage error.

Requires: python3 standard library only.
"""
import os
import re
import sys

EM_DASH = "—"
SKIP_DIRS = {"adr", "tests", "assets", "scripts", "__pycache__"}
MAX_SKILL_LINES = 500
TOC_OVER = 100
TOC_WITHIN = 20
PATH_PREFIXES = ("../", "references/", "scripts/", ".agents/")
# Subfolders of a project folder (ml-system-design, "Project folder"). A
# path into one of them is a path in a project, not in the skills tree.
PROJECT_DIRS = {"prd", "design", "adr", "spec", "modeling", "dashboard",
                "critique", "research", "monkey-mode", "monkey-mlp", "labs"}


def repo_root(start):
    """The nearest parent that holds .agents/, for .agents/... paths."""
    d = os.path.abspath(start)
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, ".agents")):
            return d
        d = os.path.dirname(d)
    return os.path.abspath(start)


def read_lines(path):
    with open(path, encoding="utf-8") as f:
        return f.read().split("\n")


def frontmatter(lines):
    """Return ({key: value}, index of the first body line)."""
    if not lines or lines[0].strip() != "---":
        return {}, 0
    meta = {}
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return meta, i + 1
        m = re.match(r"([A-Za-z_-]+):\s*(.*)", lines[i])
        if m:
            meta[m.group(1)] = m.group(2).strip()
    return meta, 0


def path_refs(line):
    """Relative paths that the line points to."""
    refs = []
    for m in re.finditer(r"\]\(([^)\s]+)\)", line):
        refs.append(m.group(1))
    for m in re.finditer(r"`([^`\s]+)", line):
        if m.group(1).startswith(PATH_PREFIXES):
            refs.append(m.group(1))
    out = []
    for r in refs:
        if r.startswith(("http:", "https:", "mailto:", "#")):
            continue
        if any(c in r for c in "<>*{}$"):
            continue
        r = r.split("#")[0].rstrip(".,;:)")
        r = re.sub(r":\d+$", "", r)
        if r:
            out.append(r)
    return out


def check_md(path, root, problems):
    try:
        lines = read_lines(path)
    except UnicodeDecodeError as e:
        problems.append((path, 0, f"not UTF-8 ({e.reason})"))
        return
    meta, body = frontmatter(lines)
    is_skill = os.path.basename(path) == "SKILL.md"
    if is_skill:
        folder = os.path.basename(os.path.dirname(path))
        if meta.get("name") != folder:
            problems.append((path, 1, f'frontmatter name is not "{folder}"'))
        if "description" not in meta:
            problems.append((path, 1, "frontmatter has no description"))
        if len(lines) > MAX_SKILL_LINES:
            problems.append((path, 0, f"SKILL.md over {MAX_SKILL_LINES} "
                                      f"lines ({len(lines)}); split it"))
    if len(lines) > TOC_OVER and not any(
            re.match(r"\s*(#+\s+)?Contents\b", l)
            for l in lines[body:body + TOC_WITHIN]):
        problems.append((path, 1, f"over {TOC_OVER} lines and no Contents "
                                  f"in the first {TOC_WITHIN} lines"))
    has_check = False
    fence = False
    base = os.path.dirname(path)
    for i, line in enumerate(lines[body:], start=body + 1):
        if EM_DASH in line:
            problems.append((path, i, "em dash"))
        if re.match(r"\s*(```|~~~)", line):
            fence = not fence
            continue
        if fence:
            continue
        if re.match(r"#+\s+.*\bCheck", line):
            has_check = True
        for ref in path_refs(line):
            target = (os.path.join(root, ref) if ref.startswith(".agents/")
                      else os.path.join(base, ref))
            if os.path.exists(target):
                continue
            first = [p for p in ref.split("/") if p not in ("..", ".")][0]
            if first in PROJECT_DIRS and first != "adr":
                continue
            problems.append((path, i, f"broken path: {ref}"))
    if is_skill and not has_check:
        problems.append((path, 0, 'no heading with "Check"'))


def check_skill_dir(skill_dir, problems):
    """references/ and scripts/ files: named in SKILL.md, deps declared."""
    skill_md = os.path.join(skill_dir, "SKILL.md")
    text = "\n".join(read_lines(skill_md))
    for sub in ("references", "scripts"):
        d = os.path.join(skill_dir, sub)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            p = os.path.join(d, name)
            if not os.path.isfile(p) or name.startswith("."):
                continue
            if f"{sub}/{name}" not in text:
                problems.append((skill_md, 0, f"{sub}/{name} is not named "
                                              "in SKILL.md"))
            if sub == "scripts" and "Requires:" not in "\n".join(
                    read_lines(p)[:60]):
                problems.append((p, 0, 'no "Requires:" line'))


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        return 2
    problems = []
    count = 0
    for top in sys.argv[1:]:
        if not os.path.isdir(top):
            print(f"{top}: not a directory", file=sys.stderr)
            return 2
        root = repo_root(top)
        own = os.path.dirname(os.path.abspath(__file__))
        for d, subdirs, names in os.walk(top):
            subdirs[:] = sorted(s for s in subdirs if s not in SKIP_DIRS
                                and os.path.join(os.path.abspath(d), s) != own)
            for name in sorted(names):
                if name.endswith(".md"):
                    check_md(os.path.join(d, name), root, problems)
                    count += 1
            if "SKILL.md" in names:
                check_skill_dir(d, problems)
    if count == 0:
        print("no .md file found", file=sys.stderr)
        return 2
    for path, n, reason in problems:
        print(f"{path}:{n}: {reason}")
    if problems:
        return 1
    print(f"OK ({count} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
