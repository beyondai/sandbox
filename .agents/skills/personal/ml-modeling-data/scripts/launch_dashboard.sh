#!/usr/bin/env bash
# Start (or reuse) a project's Streamlit dashboard on its own port.
#
# Usage:
#   launch_dashboard.sh <project-folder>
#   launch_dashboard.sh <project-folder> --stop
#
# - If dashboard/.pid is a live streamlit process for this project that
#   answers on dashboard/.port, print "RUNNING <url>" and do nothing else.
#   A PID that belongs to another process is never reused or killed.
# - Else start "uv run --project <sandbox root> streamlit run
#   dashboard/app.py" in the background:
#   reuse the port in dashboard/.port if it is a valid free port, or else
#   take the first free port from 8501 up. Write dashboard/.port and dashboard/.pid. Log to
#   dashboard/streamlit.log. Wait up to 30 s for HTTP 200, then print
#   "STARTED <url>".
# - --stop kills the process in dashboard/.pid only if it is this
#   project's dashboard, removes .pid, and prints "STOPPED".
#
# Exit code: 0 running, 1 did not answer in time, 2 usage error.
# Requires: bash, lsof, curl, uv (with streamlit, plotly, pandas in the
# sandbox venv; if missing: uv add streamlit plotly pandas at the sandbox
# root).
set -euo pipefail

usage() { awk 'NR>1 && /^#/ {sub(/^# ?/, ""); print; next} NR>1 {exit}' "$0"; exit 2; }
[ $# -ge 1 ] || usage
[ -d "$1" ] || { echo "no project folder: $1" >&2; exit 2; }
proj="$(cd "${1%/}" && pwd)"
dash="$proj/dashboard"
[ -f "$dash/app.py" ] || { echo "no dashboard/app.py in $proj" >&2; exit 2; }

# Ours = the PID is alive, its command is streamlit (or the uv wrapper that
# runs it), and it was started from this project folder.
alive() {
  [ -f "$dash/.pid" ] || return 1
  local pid; pid="$(tr -dc '0-9' < "$dash/.pid")"
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null || return 1
  ps -p "$pid" -o command= 2>/dev/null | grep -q 'streamlit run dashboard/app.py' || return 1
  [ "$(lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')" = "$proj" ]
}
valid_port() { [[ "$1" =~ ^[0-9]+$ ]] && [ "$1" -ge 1024 ] && [ "$1" -le 65535 ]; }
answers() { curl -sf -o /dev/null "http://localhost:$1"; }
port_free() { ! lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }

if [ "${2:-}" = "--stop" ]; then
  if alive; then kill "$(cat "$dash/.pid")"; fi
  rm -f "$dash/.pid"
  echo "STOPPED"
  exit 0
fi

saved_port="$(tr -d ' \t\r\n' < "$dash/.port" 2>/dev/null || true)"
if alive && valid_port "$saved_port" && answers "$saved_port"; then
  echo "RUNNING http://localhost:$saved_port"
  exit 0
fi
if alive; then kill "$(cat "$dash/.pid")" 2>/dev/null || true; sleep 1; fi

port=""
if valid_port "$saved_port" && port_free "$saved_port"; then
  port="$saved_port"
else
  p=8501
  while ! port_free "$p"; do p=$((p + 1)); done
  port="$p"
fi
echo "$port" > "$dash/.port"

# Use the shared sandbox venv, also for a project outside the repo.
root="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
cd "$proj"
nohup uv run --project "$root" streamlit run dashboard/app.py --server.headless true \
  --server.port "$port" > "$dash/streamlit.log" 2>&1 &
echo $! > "$dash/.pid"

for _ in $(seq 1 30); do
  if answers "$port"; then echo "STARTED http://localhost:$port"; exit 0; fi
  sleep 1
done
echo "NOT ANSWERING http://localhost:$port (see dashboard/streamlit.log)" >&2
exit 1
