#!/usr/bin/env bash
set -euo pipefail

HOST="0.0.0.0"
PORT="${PORT:-8787}"

exec python scripts/resume_tailor_web.py --host "$HOST" --port "$PORT"
