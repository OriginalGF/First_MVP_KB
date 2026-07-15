#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT_DIR/frontend"
if [ -f package.json ]; then
  npm install
  npm run build
fi

cd "$ROOT_DIR"
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
