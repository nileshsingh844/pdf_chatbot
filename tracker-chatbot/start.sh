#!/usr/bin/env bash
set -e

echo "Starting FastAPI backend on :8000..."
/app/backend/.venv/bin/uvicorn backend.app.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level info &

echo "Starting Next.js frontend on :7860..."
cd /app/frontend
npm run start -- --port 7860 --hostname 0.0.0.0
