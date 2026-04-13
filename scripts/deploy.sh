#!/usr/bin/env bash
# deploy.sh — deploy glowing-robot to a VPS using Docker Compose
#
# Prerequisites on the server:
#   - Docker + Docker Compose v2
#   - Git
#   - infra/.env.prod with real values (never committed)
#
# Usage (from repo root on your server):
#   bash scripts/deploy.sh
#
# First time:
#   git clone https://github.com/Evode-Manirahari/glowing-robot
#   cd glowing-robot
#   cp infra/.env.example infra/.env.prod
#   nano infra/.env.prod          # fill in POSTGRES_PASSWORD, SECRET_KEY, ANTHROPIC_API_KEY
#   bash scripts/deploy.sh --init

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE="docker compose -f $ROOT/infra/docker-compose.prod.yml --env-file $ROOT/infra/.env.prod"
INIT=false

for arg in "$@"; do
  [[ "$arg" == "--init" ]] && INIT=true
done

echo ""
echo "=== glowing-robot deploy ==="
echo ""

# Pull latest
echo "[1/4] Pulling latest code..."
git -C "$ROOT" pull --ff-only
echo "      Done."

# Build images
echo "[2/4] Building Docker images..."
$COMPOSE build --quiet
echo "      Done."

# Start / restart services
echo "[3/4] Starting services..."
$COMPOSE up -d --remove-orphans
echo "      Done."

# First-time DB init
if [ "$INIT" = true ]; then
  echo "[4/4] Initialising database (first deploy)..."
  sleep 5  # wait for DB to be healthy
  $COMPOSE exec -T backend python scripts/reset_db.py <<< "yes"
  echo "      Database ready."
else
  echo "[4/4] Skipping DB init (use --init on first deploy)."
fi

echo ""
echo "  App:     http://$(curl -s ifconfig.me 2>/dev/null || echo 'your-server-ip')"
echo "  API:     http://$(curl -s ifconfig.me 2>/dev/null || echo 'your-server-ip')/docs"
echo "  Logs:    docker compose -f infra/docker-compose.prod.yml logs -f"
echo ""
