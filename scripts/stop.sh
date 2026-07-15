#!/usr/bin/env bash
set -euo pipefail

if command -v lsof >/dev/null 2>&1; then
  lsof -i :8000 -t | xargs -r kill
elif command -v fuser >/dev/null 2>&1; then
  fuser -k 8000/tcp
else
  echo "No supported process killer found for port 8000." >&2
fi
