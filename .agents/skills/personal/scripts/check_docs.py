#!/usr/bin/env python3
"""Check the docs folder for style and for consistency with the skills.

Usage (from the sandbox root):
  python3 .agents/skills/personal/scripts/check_docs.py \
      [--docs docs] [--skills .agents/skills/personal]

Style (docs are for people: docs/SKILL-STYLE-GUIDE.md, "Writing rules"):
  - .md: the check_doc.py rules (80 columns, wide tables, em dashes, code
    fences);
  - .txt: 80 columns and em dashes;
  - a file over 100 lines has "Contents" in its first 20 lines;
  - each "](#anchor)" link matches a heading in the same file;
  - each relative link, and each backtick path that starts with .agents/
    or docs/, resolves (globs and <placeholders> are skipped).
Consistency with the skills:
  - each skill folder in the skills dir is named in a doc, by its full
    name or its short form (ml-system-design-x -> sd-x, ml-modeling-x ->
    mm-x);
  - each ADR number cited in a doc as "(00NN" exists in <skills>/adr/;
  - each ADR file in <skills>/adr/ has a row in <skills>/README.md.
The checks that need judgment are the docs checklist in
docs/SKILL-STYLE-GUIDE.md, "How to check".

Prints "file:line: reason" for each failure, or "OK (<n> files)".
Exit code 0 when clean, 1 on a failure, 2 on a usage error.

Requires: python3 standard library only. Imports check_doc.py from
ml-system-design/scripts/ in the skills dir.
"""
import argparse
import importlib.util
import os
import re
import sys

EM_DASH = "—"
LIMIT = 80
TOC_OVER = 100
TOC_WITHIN = 20


def load_check_doc(skills):
    path = os.path.join(skills, "ml-system-design", "scripts", "check_doc.py")
    spec = importlib.util.spec_from_file_location("check_doc", path)
    if spec is None or not os.path.isfile(path):
        print(f"{path}: not found", file=sys.stderr)
        sys.exit(2)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def slug(heading):
    """GitHub anchor for a heading."""
    h = re.sub(r"[`*_]", "", heading.strip().lower())
    return re.sub(r"[^\w\- ]", "", h).replace(" ", "-")


def style(path, lines, check_doc, root):
    problems = []
    if path.endswith(".md"):
        problems += check_doc.check(path, [], False)
    else:
        for i, line in enumerate(lines, 1):
            if EM_DASH in line:
                problems.append((i, "em dash"))
            if len(line) > LIMIT and " " in line.strip():
                problems.append((i, f"line over {LIMIT} columns ({len(line)})"))
    if len(lines) > TOC_OVER and not any(
            re.match(r"\s*(#+\s+)?Contents\b", l) for l in lines[:TOC_WITHIN]):
        problems.append((1, f"over {TOC_OVER} lines and no Contents in the "
                            f"first {TOC_WITHIN} lines"))
    if not path.endswith(".md"):
        return problems
    text = "\n".join(lines)
    anchors = {slug(h) for h in re.findall(r"^#+ (.+)$", text, re.M)}
    base = os.path.dirname(path)
    fence = False
    for i, line in enumerate(lines, 1):
        if re.match(r"\s*(```|~~~)", line):
            fence = not fence
            continue
        if fence:
            continue
        for a in re.findall(r"\]\(#([^)]+)\)", line):
            if a not in anchors:
                problems.append((i, f"broken anchor: #{a}"))
        for ref in re.findall(r"\]\(([^)#\s]+)\)", line):
            if ref.startswith(("http:", "https:", "mailto:")):
                continue
            if not os.path.exists(os.path.join(base, ref)):
                problems.append((i, f"broken link: {ref}"))
        for ref in re.findall(r"`((?:\.agents|docs)/[^`\s]+)", line):
            if any(c in ref for c in "*<>{}"):
                continue
            ref = ref.rstrip(".,;:")
            if not os.path.exists(os.path.join(root, ref)):
                problems.append((i, f"broken path: {ref}"))
    return problems


def short_names(name):
    out = {name}
    for long, short in (("ml-system-design", "sd"), ("ml-modeling", "mm")):
        if name == long:
            out.add(short)
        elif name.startswith(long + "-"):
            out.add(short + name[len(long):])
    return out


def consistency(docs_text, skills, readme):
    problems = []
    for name in sorted(os.listdir(skills)):
        if not os.path.isfile(os.path.join(skills, name, "SKILL.md")):
            continue
        if not any(re.search(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])",
                             docs_text) for n in short_names(name)):
            problems.append((readme, 0, f"skill {name} is not named in docs/"))
    adr_dir = os.path.join(skills, "adr")
    adrs = {f[:4] for f in os.listdir(adr_dir) if re.match(r"\d{4}-", f)}
    for num in sorted(set(re.findall(r"\((0\d{3})\b", docs_text))):
        if num not in adrs:
            problems.append(("docs/", 0, f"cites ADR {num}, which does not exist"))
    with open(readme, encoding="utf-8") as f:
        index = f.read()
    for num in sorted(adrs):
        if f"| {num} |" not in index:
            problems.append((readme, 0, f"ADR {num} has no row in the index"))
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--docs", default="docs")
    ap.add_argument("--skills", default=".agents/skills/personal")
    args = ap.parse_args()
    for d in (args.docs, args.skills):
        if not os.path.isdir(d):
            print(f"{d}: not a directory", file=sys.stderr)
            return 2
    root = os.path.abspath(os.path.join(args.skills, "..", "..", ".."))
    check_doc = load_check_doc(args.skills)
    files = sorted(os.path.join(args.docs, f) for f in os.listdir(args.docs)
                   if f.endswith((".md", ".txt")))
    if not files:
        print("no .md or .txt file found", file=sys.stderr)
        return 2
    failed = 0
    docs_text = ""
    for path in files:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        docs_text += text + "\n"
        for n, reason in style(path, text.split("\n"), check_doc, root):
            print(f"{path}:{n}: {reason}")
            failed += 1
    readme = os.path.join(args.skills, "README.md")
    for path, n, reason in consistency(docs_text, args.skills, readme):
        print(f"{path}:{n}: {reason}")
        failed += 1
    if failed:
        return 1
    print(f"OK ({len(files)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
