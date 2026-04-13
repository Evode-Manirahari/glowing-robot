# Architecture

## Overview

glowing-robot is a software-first robot QA and validation platform. It has no hardware dependency — customers bring their own robots and upload logs.

## System layers

```
┌──────────────────────────────────────────────┐
│  webapp (React + Vite, port 5173)            │
│  Mission list · Upload · Replay viewer · AI  │
└─────────────────────┬────────────────────────┘
                      │ REST + JSON
┌─────────────────────▼────────────────────────┐
│  backend (FastAPI, port 8000)                │
│  /auth  /missions  /jobs  /evals             │
│  Background job runner (FastAPI tasks)       │
└──────┬──────────────┬──────────────┬─────────┘
       │              │              │
  ┌────▼────┐   ┌─────▼─────┐  ┌────▼────┐
  │PostgreSQL│   │   Redis   │  │ File    │
  │(missions,│   │(future    │  │ storage │
  │ jobs,    │   │ queue)    │  │uploads/ │
  │ reports) │   └───────────┘  │runs/    │
  └──────────┘                  └─────────┘
       │
┌──────▼──────────────────────────────────────┐
│  sim/replay/engine.py  (pure Python)        │
│  Geometry-based collision + deviation check │
│  → MuJoCo physics when fidelity needed      │
└─────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│  evals/  (metrics + report generation)      │
│  compute.py  ·  generator.py               │
└─────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│  Claude API  (AI failure summaries)         │
│  claude-sonnet-4-6 via anthropic SDK        │
└─────────────────────────────────────────────┘
```

## Request flow: upload → eval

1. User uploads `.json` or `.csv` log via `POST /missions/upload`
2. Backend saves file to `uploads/<mission_id>/`
3. `Job` record created in DB (type=replay, status=queued)
4. FastAPI BackgroundTask fires `job_runner.run_job(job_id)`
5. Job runner: calls `eval_service.run_replay(log_path)` → runs sim engine
6. Metrics computed by `evals/metrics/compute.py`
7. Claude generates a natural-language failure summary
8. `EvalReport` persisted to DB; mission status → "evaluated"
9. Frontend polls `/jobs/{job_id}` every 1.5s until `status=completed`
10. Frontend loads `/evals/{mission_id}/report` and `/missions/{mission_id}/replay`
11. `ReplayViewer` renders SVG trajectory with play control

## Log formats accepted

| Format | Extension | Parser |
|---|---|---|
| Native (our schema) | `.json` | `robot_api/parsers/json_parser.py` |
| ROS-bag-derived poses | `.json` (with `poses` key) | `robot_api/parsers/json_parser.py` |
| Tabular trajectory | `.csv` (columns: t, x, y, [theta, velocity]) | `robot_api/parsers/csv_parser.py` |

## Sim engine upgrade path

Current MVP uses pure-geometry checks (no external dependency).
To upgrade to full physics:

1. Install MuJoCo: `pip install mujoco`
2. Add a scene XML to `sim/environments/`
3. Swap `engine.py` collision check for `mujoco.MjModel` contact detection
4. No other layer changes needed — the `ReplayResult` interface stays the same

## Auth

JWT bearer tokens. 7-day expiry. Tokens stored in `localStorage` on the client.
All API routes except `/health` and `/auth/register` and `/auth/login` require a valid token.

## Scaling path

Current: single FastAPI process with BackgroundTasks.
When needed: replace BackgroundTasks with a Redis queue + separate Celery or ARQ worker.
The `job_runner.py` logic moves intact — only the dispatch mechanism changes.
