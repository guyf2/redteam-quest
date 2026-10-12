#!/usr/bin/env bash
# One-time setup for RedTeam Quest. Safe to re-run: every step skips what is already done.
#   ./setup.sh                 full setup
#   ./setup.sh --skip-models   don't pull the Ollama models
#   ./setup.sh --skip-warmup   don't even prepare the small MNIST target (done on first use instead)
#   ./setup.sh --full-warmup   also pre-download CIFAR-10 + CLIP (~0.7 GB; otherwise fetched when you open a multimodal level)
#   ./setup.sh --no-launcher   don't add an app-menu launcher
set -u
cd "$(dirname "$(readlink -f "$0")")" || exit 1
ROOT=$PWD
VENV="$ROOT/labs/00-setup/.venv"
MODELS=(llama3.2:3b qwen2.5vl:7b)
SKIP_MODELS=0; SKIP_WARMUP=0; FULL_WARMUP=0; NO_LAUNCHER=0
for a in "$@"; do
  case "$a" in
    --skip-models) SKIP_MODELS=1 ;;
    --skip-warmup) SKIP_WARMUP=1 ;;
    --full-warmup) FULL_WARMUP=1 ;;
    --no-launcher) NO_LAUNCHER=1 ;;
    -h|--help) sed -n '2,6p' "$0"; exit 0 ;;
    *) echo "Unknown option: $a (try --help)"; exit 1 ;;
  esac
done

ok()   { printf '  \033[32mok\033[0m   %s\n' "$*"; }
warn() { printf '  \033[33mWARN\033[0m %s\n' "$*"; WARNINGS=$((WARNINGS + 1)); }
step() { printf '\n\033[1m%s\033[0m\n' "$*"; }
WARNINGS=0

step "1/6  Python"
PYBIN=""
for c in python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then PYBIN=$c; break; fi
done
if [ -z "$PYBIN" ]; then echo "Python 3.10 or newer is required (3.12 recommended). Install it and re-run."; exit 1; fi
ok "using $($PYBIN --version) ($PYBIN)"

step "2/6  Python environment ($VENV)"
if [ ! -x "$VENV/bin/python" ]; then
  "$PYBIN" -m venv "$VENV" || { echo "Could not create the virtual environment (on Debian/Ubuntu: sudo apt install python3-venv)."; exit 1; }
fi
if command -v uv >/dev/null 2>&1; then
  uv pip install --python "$VENV/bin/python" -r requirements.txt || { echo "Dependency install failed."; exit 1; }
else
  "$VENV/bin/python" -m pip install --upgrade pip >/dev/null 2>&1
  "$VENV/bin/python" -m pip install -r requirements.txt || { echo "Dependency install failed."; exit 1; }
fi
ok "dependencies installed"

step "3/6  GPU"
if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
  ok "NVIDIA GPU: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -1)"
  "$VENV/bin/python" -c 'import torch,sys; sys.exit(0 if torch.cuda.is_available() else 1)' 2>/dev/null \
    && ok "PyTorch can use it" \
    || warn "PyTorch cannot use the GPU. If nvidia-smi errors with 'Driver/library version mismatch', reboot; otherwise update your NVIDIA driver."
else
  warn "No working NVIDIA GPU detected. The game runs, but the model-based levels will be very slow on CPU. A GPU with ~12 GB of VRAM is recommended."
fi

step "4/6  Ollama (local models the live-target levels attack)"
if ! command -v ollama >/dev/null 2>&1; then
  warn "Ollama is not installed. Get it from https://ollama.com/download, then re-run ./setup.sh. Until then the chatbot / vision-language levels will not work."
elif [ "$SKIP_MODELS" = 1 ]; then
  ok "skipping model downloads (--skip-models)"
elif ! ollama list >/dev/null 2>&1; then
  warn "Ollama is installed but its server is not running. Start it (e.g. 'ollama serve' or 'sudo systemctl start ollama') and re-run ./setup.sh."
else
  for m in "${MODELS[@]}"; do
    if ollama list 2>/dev/null | awk 'NR>1 {print $1}' | grep -qx "$m"; then ok "$m already pulled"
    else echo "  pulling $m ..."; ollama pull "$m" && ok "$m pulled" || warn "could not pull $m"; fi
  done
fi

step "5/6  Claude Code (powers the Build agent, Guide and Co-pilot with YOUR account)"
if command -v claude >/dev/null 2>&1; then
  ok "found $(command -v claude)"
  echo "       Make sure you are logged in: run 'claude' once in a terminal and sign in with YOUR OWN account."
  echo "       The three chat helpers run on whatever account is logged in on this computer."
else
  warn "The 'claude' command was not found. Install Claude Code (https://docs.claude.com/en/docs/claude-code/setup), run it once to sign in, then re-run ./setup.sh. Without it the game works but the three chat helpers show an error."
fi

step "6/6  Warm-up (small MNIST target; CIFAR-10 + CLIP only with --full-warmup)"
if [ "$SKIP_WARMUP" = 1 ]; then
  ok "skipping warm-up (--skip-warmup); it happens lazily on first use instead"
else
  ( cd game && FULL="$FULL_WARMUP" "$VENV/bin/python" -c '
import os, sys; sys.path.insert(0, ".")
from levels import common
common.target(); print("  MNIST target ready")
if os.environ.get("FULL") == "1":
    from levels import clipkit
    clipkit._load(); print("  CLIP + CIFAR-10 ready")
' 2>&1 | grep -v "Warning\|warn" ) && ok "warm-up done" || warn "warm-up failed (needs internet on first run); the game will retry on first use"
fi

if [ "$NO_LAUNCHER" = 0 ] && command -v xdg-open >/dev/null 2>&1; then
  APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
  mkdir -p "$APPS" && cat > "$APPS/redteam-quest.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=RedTeam Quest
Comment=Start the AI red-teaming game and open it in your browser
Exec=$ROOT/start-game.sh
Icon=applications-games
Terminal=false
Categories=Education;Game;
EOF
  ok "added an app-menu launcher (RedTeam Quest)"
fi

printf '\n'
if [ "$WARNINGS" -eq 0 ]; then printf '\033[32mAll set.\033[0m'; else printf '\033[33mSetup finished with %s warning(s) above.\033[0m' "$WARNINGS"; fi
echo " Start the game with:  ./start-game.sh   (or ./play.sh)"
