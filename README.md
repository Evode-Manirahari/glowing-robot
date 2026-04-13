# glowing-robot

Robot QA and validation platform. Upload a mission log, replay it in simulation, detect failures, compare policy versions, and get an AI-generated report — without touching a terminal.

Built for warehouse and logistics teams that already have robots and need a systematic way to test software before deployment.

---

## What it does

- **Mission replay** — load a robot trajectory log and replay it frame by frame in a 2D sim engine. Detects collisions, path deviations, and incomplete waypoint coverage.
- **Pass/fail verdicts** — every run gets a scored verdict with annotated anomalies.
- **AI analysis** — Claude reads the metrics and writes a plain-English explanation of what went wrong and where to look.
- **Policy comparison** — compare two runs side by side with a delta table and AI-generated diff. Catch regressions before they reach the floor.
- **API keys** — upload logs and poll results from your CI/CD pipeline without a browser.
- **Report download** — export any evaluation as a structured JSON file.

---

## Supported log formats

| Format | Description |
|--------|-------------|
| `.bag` | ROS1 bag files |
| `.mcap` / `.db3` | ROS2 bag files |
| `.json` | Native glowing-robot format or ROS-bag-derived |
| `.csv` | Columns: `t, x, y, [theta], [velocity]` |

Not sure which topics are in your bag? Run:
```bash
python scripts/bag_info.py path/to/mission.bag
```

---

## Stack

- **Sim engine** — pure Python geometry replay (MuJoCo-ready, no install required for MVP)
- **Backend** — Python 3.13 + FastAPI + PostgreSQL + Redis
- **Frontend** — React + Vite + TypeScript
- **AI** — Claude via Anthropic SDK
- **Infra** — Docker Compose

---

## Quick start (local dev)

**Prerequisites:** Python 3.11+, Node 18+, Docker

```bash
git clone https://github.com/Evode-Manirahari/glowing-robot
cd glowing-robot

# Start Postgres + Redis, install deps
bash scripts/dev.sh

# Terminal 1 — backend
cd backend
source .venv/bin/activate
ANTHROPIC_API_KEY=sk-ant-... uvicorn app.main:app --reload

# Terminal 2 — frontend
cd webapp
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

### Try it without the backend

```bash
# Replay a warehouse scenario
python scripts/demo_replay.py sim/scenarios/warehouse_basic.json
python scripts/demo_replay.py sim/scenarios/warehouse_collision.json

# Compare two runs side by side
python scripts/demo_compare.py sim/scenarios/warehouse_basic.json sim/scenarios/warehouse_collision.json
```

---

## Production deploy

**Prerequisites:** A Linux VPS with Docker + Docker Compose v2.

```bash
git clone https://github.com/Evode-Manirahari/glowing-robot
cd glowing-robot

# 1. Set secrets
cp infra/.env.prod.example infra/.env.prod
nano infra/.env.prod   # fill in POSTGRES_PASSWORD, SECRET_KEY, ANTHROPIC_API_KEY

# 2. Deploy (first time)
bash scripts/deploy.sh --init

# 3. Every deploy after that
bash scripts/deploy.sh
```

The app runs on port 80. nginx serves the React SPA and proxies API calls to the backend.

---

## CI/CD integration

Generate an API key in **Settings → API Keys**, then upload logs from your pipeline:

```bash
# Upload a mission log
curl -X POST https://your-host/missions/upload \
  -H "X-Api-Key: gr_live_..." \
  -F "name=deploy-v2.1.3" \
  -F "robot_type=AMR" \
  -F "log_file=@mission.json"

# Poll for result
curl https://your-host/missions/{mission_id} \
  -H "X-Api-Key: gr_live_..."
```

---

## Project structure

```
sim/          Replay engine — geometry checks, MuJoCo-ready
robot_api/    Log parsers — JSON, CSV, ROS1 .bag, ROS2 .mcap/.db3
backend/      FastAPI — auth, missions, jobs, evals, API keys
webapp/       React app — mission list, replay viewer, compare, settings
evals/        Metrics computation and report generation
infra/        Docker Compose (dev + prod), nginx config
scripts/      Runnable demo and utility scripts
```

---

## Scripts

| Script | Description |
|--------|-------------|
| `scripts/dev.sh` | Start local dev stack |
| `scripts/demo_replay.py <log>` | Replay a mission from the CLI |
| `scripts/demo_compare.py <a> <b>` | Compare two missions from the CLI |
| `scripts/bag_info.py <bag>` | Inspect ROS bag topics |
| `scripts/reset_db.py` | Drop and recreate all tables (dev only) |
| `scripts/deploy.sh` | Deploy to production VPS |

---

## License

MIT
