#!/bin/bash
# Start the research console on this machine only: http://127.0.0.1:8770
cd "$(dirname "$0")/.." || exit 1
PY=${WF_PYTHON:-/home/khjtony/workspace/wave_front/.venv/bin/python}
PYTHONPATH=. exec "$PY" -m console.server --port "${WF_CONSOLE_PORT:-8770}"
