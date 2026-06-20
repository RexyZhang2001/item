#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VENV="${VENV_DIR:-$ROOT/.venv}"
if [[ ! -f "$VENV/bin/activate" ]]; then
  echo "请先运行: bash scripts/setup_linux.sh"
  exit 1
fi
# shellcheck source=/dev/null
source "$VENV/bin/activate"

URL="${1:-rtmp://10.148.1.22/live/test}"
OUT="${OUT_DIR:-$ROOT/output/stream_test}"

ARGS=(--url "$URL" --out "$OUT")
if [[ "${STREAM_ONLY:-0}" == "1" ]]; then
  ARGS+=(--stream-only)
fi

exec python test_stream_detect.py "${ARGS[@]}"
