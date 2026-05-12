#!/bin/bash
set -euo pipefail

# Only run in remote Claude Code on the web sessions
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo "==> Installing Node.js dependencies..."
npm install

echo "==> Installing Python dependencies via uv..."
if command -v uv &>/dev/null; then
  uv sync
else
  pip install -r <(uv export --no-hashes 2>/dev/null || echo "") 2>/dev/null || pip install fastapi uvicorn python-dotenv httpx pydantic
fi

echo "==> Session dependencies ready."
