#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VENV="${VENV_DIR:-$ROOT/.venv}"
if [[ ! -f "$VENV/bin/activate" ]]; then
  echo "请先运行: bash scripts/setup_linux.sh api"
  exit 1
fi
# shellcheck source=/dev/null
source "$VENV/bin/activate"

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8080}"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

exec uvicorn hiagent_api:app --host "$HOST" --port "$PORT"
