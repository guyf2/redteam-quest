#!/usr/bin/env bash
# Double-click launcher: starts RedTeam Quest if it is not running, then opens it in your browser.
ROOT="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
URL=http://127.0.0.1:8765
PY="$ROOT/labs/00-setup/.venv/bin/python"
LOG="${XDG_CACHE_HOME:-$HOME/.cache}/redteam-quest.log"
# a desktop/dock launch has a minimal PATH: add the usual places the claude CLI lives
for d in "$HOME"/.nvm/versions/node/*/bin "$HOME/.local/bin" /usr/local/bin; do [ -d "$d" ] && PATH="$d:$PATH"; done
export PATH
mkdir -p "$(dirname "$LOG")"

[ -x "$PY" ] || { notify-send "RedTeam Quest" "Not set up yet: run ./setup.sh first." 2>/dev/null; echo "Not set up yet: run ./setup.sh first." >&2; exit 1; }

up() { curl -s -m 2 -o /dev/null "$URL/api/state"; }

if ! up; then
  cd "$ROOT" || exit 1
  setsid nohup "$PY" game/server.py --no-browser >"$LOG" 2>&1 &
  for _ in $(seq 1 30); do up && break; sleep 1; done
fi

if up; then
  xdg-open "$URL" >/dev/null 2>&1
else
  notify-send "RedTeam Quest" "The game did not start. Details: $LOG" 2>/dev/null
  exit 1
fi
