#!/usr/bin/env bash
# ./play.sh [--no-browser]  -> web UI (opens your browser)
# ./play.sh map|start N|check N|hint N|quiz N  -> terminal version
cd "$(dirname "$0")" || exit 1
PY=labs/00-setup/.venv/bin/python
[ -x "$PY" ] || { echo "Not set up yet: run ./setup.sh first." >&2; exit 1; }
case "${1:-}" in
  ""|--no-browser) exec $PY game/server.py "$@" ;;
  *) exec $PY game/play.py "$@" ;;
esac
