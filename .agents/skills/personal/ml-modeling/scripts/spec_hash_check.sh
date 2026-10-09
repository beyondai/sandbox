#!/usr/bin/env bash
# Compare a project's spec hashes with its current design docs.
#
# Usage:
#   spec_hash_check.sh <project-folder>
#   spec_hash_check.sh <project-folder> --refresh <prd|high-level>
#
# Reads spec/<topic>.md (the only .md file in spec/). Its first lines hold
# "prd-hash: <sha>" and "high-level-hash: <sha>". The docs are
# prd/<topic>.md and design/high-level.md. Git runs in the project's own
# repository, so the project must be inside a git repository.
#
# Output, one line for each doc:
#   MATCH <file>
#   CHANGED <file>    then "  OLD <sha> NEW <sha>" (full SHAs) and the
#                     diff stat; run "git diff <old> <new>" for the content
#   NOHASH <spec>     the hash line is missing: stop and ask the user
#   MISSING <file>    the doc does not exist: stop and ask the user
# --refresh stores the current blob (git hash-object -w) and rewrites that
# hash line in the spec.
#
# Exit code: 0 all match (or refresh done), 1 a doc changed, is missing,
# or has no hash, 2 usage error or no spec/ (synthesize the spec first).
# Requires: bash, git.
set -euo pipefail

usage() { awk 'NR>1 && /^#/ {sub(/^# ?/, ""); print; next} NR>1 {exit}' "$0"; exit 2; }
die() { echo "$1" >&2; exit 2; }
[ $# -ge 1 ] || usage
proj="${1%/}"
[ -d "$proj" ] || die "no project folder: $proj"
[ -d "$proj/spec" ] || die "no spec/ in $proj (synthesize the spec first)"
git -C "$proj" rev-parse --git-dir >/dev/null 2>&1 \
  || die "$proj is not inside a git repository (run git init there)"
g() { git -C "$proj" "$@"; }

shopt -s nullglob
specs=("$proj"/spec/*.md)
[ ${#specs[@]} -eq 1 ] || die "expected exactly one spec/*.md in $proj, found ${#specs[@]}"
spec="${specs[0]}"
topic="$(basename "$spec" .md)"

doc_for() {
  case "$1" in
    prd) echo "$proj/prd/$topic.md" ;;
    high-level) echo "$proj/design/high-level.md" ;;
    *) die "unknown key '$1' (use prd or high-level)" ;;
  esac
}
old_hash() { sed -n "s/^$1-hash:[[:space:]]*//p" "$spec" | head -1 | tr -d ' \t\r'; }
abspath() { (cd "$(dirname "$1")" && echo "$(pwd)/$(basename "$1")"); }

if [ "${2:-}" = "--refresh" ]; then
  key="${3:-}"; [ -n "$key" ] || usage
  doc="$(doc_for "$key")"
  [ -f "$doc" ] || die "cannot refresh: $doc does not exist"
  grep -q "^$key-hash:" "$spec" || die "no $key-hash line in $spec"
  new="$(g hash-object -w "$(abspath "$doc")")"
  content="$(sed "s/^$key-hash:.*/$key-hash: $new/" "$spec")"
  printf '%s\n' "$content" > "$spec"   # rewrite in place; keeps the file mode
  echo "REFRESHED $doc $new"
  exit 0
fi

status=0
for key in prd high-level; do
  doc="$(doc_for "$key")"
  old="$(old_hash "$key")"
  if [ -z "$old" ]; then echo "NOHASH $spec ($key-hash line missing)"; status=1; continue; fi
  if [ ! -f "$doc" ]; then echo "MISSING $doc"; status=1; continue; fi
  new="$(g hash-object "$(abspath "$doc")")"
  if [ "$old" = "$new" ]; then
    echo "MATCH $doc"
  else
    echo "CHANGED $doc"
    echo "  OLD $old NEW $new"
    g hash-object -w "$(abspath "$doc")" >/dev/null
    if g cat-file -e "$old" 2>/dev/null; then
      g diff --stat "$old" "$new" | sed 's/^/  /'
    else
      echo "  (old blob is not in this repository; no diff)"
    fi
    status=1
  fi
done
exit $status
