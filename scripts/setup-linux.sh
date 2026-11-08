#!/usr/bin/env bash
# Local, CPU-first setup. No sudo and no changes to system Python.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
PYTHON="${PYTHON:-python3}"
"$PYTHON" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
# Installing PyTorch from the CPU wheel index avoids NVIDIA's large CUDA libraries
# on Linux machines using AMD or no discrete GPU.
.venv/bin/python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install -r requirements-rag.txt
printf '\nSetup complete. Start DeskMind with: bash scripts/run-local.sh\n'
