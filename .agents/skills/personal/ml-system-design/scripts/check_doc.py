#!/usr/bin/env python3
"""Check ml-* output docs against the "Output docs" format rules.

Usage:
  python3 check_doc.py <file|dir> [<file|dir> ...] [--sections "A,B"]
                       [--allow-wide-tables]

Checks each .md file (a directory is searched for .md files):
  - a prose line longer than 80 display columns (fenced code is exempt;
    ``` and ~~~ fences of any length; an unclosed fence is an error);
  - a table row longer than 80 columns (write headed paragraphs instead);
  - an em dash (use "-" or rewrite the sentence);
  - with --sections: each named heading exists (a leading "1. " in the
    heading is ignored; the name must match the heading start exactly).
YAML frontmatter is skipped. A line with no space (a long URL or path) is
exempt from the length check.

Prints "file:line: reason" for each failure, or "OK (<n> files)".
Exit code 0 when clean, 1 on a failure, 2 on a usage error (including no
.md file found).

Requires: python3 standard library only.
"""
import argparse
import os
import re
import sys
import unicodedata

LIMIT = 80
EM_DASH = "—"


def md_files(paths):
    for path in paths:
        if os.path.isdir(path):
            for root, _, names in os.walk(path):
                for name in sorted(names):
                    if name.endswith(".md"):
                        yield os.path.join(root, name)
        elif os.path.isfile(path):
            yield path
        else:
            print(f"{path}: not found", file=sys.stderr)
            sys.exit(2)


def width(text):
    """Display columns: wide East Asian characters count as 2."""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1
               for c in text)


def check(path, sections, allow_wide_tables):
    problems = []
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().split("\n")
    except UnicodeDecodeError as e:
        return [(0, f"not UTF-8 ({e.reason} at byte {e.start})")]
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break
    fence = None          # (char, length) of the open fence, or None
    fence_line = 0
    headings = []
    for i in range(start, len(lines)):
        line = lines[i]
        n = i + 1
        if EM_DASH in line:
            problems.append((n, "em dash"))
        m = re.match(r"\s*(`{3,}|~{3,})(.*)$", line)
        if m:
            char, length = m.group(1)[0], len(m.group(1))
            if fence is None:
                fence, fence_line = (char, length), n
                continue
            if char == fence[0] and length >= fence[1] and not m.group(2).strip():
                fence = None
                continue
        if fence is not None:
            continue
        m = re.match(r"#+\s+(.*)", line)
        if m:
            headings.append(m.group(1).strip().lower())
        w = width(line)
        if w <= LIMIT or " " not in line.strip():
            continue
        if line.lstrip().startswith("|"):
            if not allow_wide_tables:
                problems.append((n, f"table row over {LIMIT} columns "
                                    f"({w}); use headed paragraphs"))
        else:
            problems.append((n, f"line over {LIMIT} columns ({w})"))
    if fence is not None:
        problems.append((fence_line, "code fence is never closed"))
    for name in sections:
        want = name.lower()
        if not any(re.sub(r"^\d+\.\s+", "", h) == want
                   or re.match(re.escape(want) + r"\b", re.sub(r"^\d+\.\s+", "", h))
                   for h in headings):
            problems.append((0, f'missing section "{name}"'))
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--sections", default="",
                    help="comma-separated headings that must exist")
    ap.add_argument("--allow-wide-tables", action="store_true",
                    help="do not flag wide table rows (skill files)")
    args = ap.parse_args()
    sections = [s.strip() for s in args.sections.split(",") if s.strip()]
    files = list(md_files(args.paths))
    if not files:
        print("no .md file found", file=sys.stderr)
        return 2
    failed = 0
    for path in files:
        for n, reason in check(path, sections, args.allow_wide_tables):
            print(f"{path}:{n}: {reason}")
            failed += 1
    if failed:
        return 1
    print(f"OK ({len(files)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
