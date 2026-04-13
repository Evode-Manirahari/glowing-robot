#!/usr/bin/env bash
# dev.sh — start the full local dev stack
# Usage: bash scripts/dev.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo ""
echo "=== glowing-robot dev startup ==="
echo ""

# 1. Backend Python env
if [ ! -d "$ROOT/backend/.venv" ]; then
  echo "[1/4] Creating Python venv..."
  python3 -m venv "$ROOT/backend/.venv"
  "$ROOT/backend/.venv/bin/pip" install -e "$ROOT/backend[dev]" -q
  echo "      Done."
else
  echo "[1/4] Python venv exists, skipping."
fi

# 2. Webapp node modules
if [ ! -d "$ROOT/webapp/node_modules" ]; then
  echo "[2/4] Installing webapp dependencies (npm)..."
  cd "$ROOT/webapp" && npm install -q
  echo "      Done."
else
  echo "[2/4] node_modules exists, skipping."
fi

# 3. Start Postgres + Redis via Docker Compose
echo "[3/4] Starting Postgres + Redis..."
cd "$ROOT/infra"
if [ -f ".env" ]; then
  docker compose --env-file .env up db redis -d --quiet-pull
else
  docker compose up db redis -d --quiet-pull
fi
echo "      Waiting for Postgres to be healthy..."
until docker compose exec -T db pg_isready -U postgres > /dev/null 2>&1; do sleep 1; done
echo "      Ready."

# 4. Instructions
echo ""
echo "[4/4] Start the backend and frontend in separate terminals:"
echo ""
echo "  Backend:"
echo "    cd $ROOT/backend"
echo "    source .venv/bin/activate"
echo "    ANTHROPIC_API_KEY=sk-ant-... uvicorn app.main:app --reload"
echo ""
echo "  Frontend:"
echo "    cd $ROOT/webapp"
echo "    npm run dev"
echo ""
echo "  API docs: http://localhost:8000/docs"
echo "  App:      http://localhost:5173"
echo ""
echo "  Demo CLI (no backend needed):"
echo "    python3 scripts/demo_replay.py sim/scenarios/warehouse_basic.json"
echo ""
