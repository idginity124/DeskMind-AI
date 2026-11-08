#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
if [[ ! -x .venv/bin/python ]]; then
  printf 'Python environment not found. Run: bash scripts/setup-linux.sh\n' >&2
  exit 1
fi
exec .venv/bin/python -m uvicorn api:app --host 127.0.0.1 --port 8000
