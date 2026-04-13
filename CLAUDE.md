# CLAUDE.md — glowing-robot

## What this repo is

glowing-robot is a **robot QA and validation platform**. It lets robotics teams upload mission logs, replay them in simulation, detect failures, compare policy versions, and generate deployment reports. It is a software product — we do not manufacture robots.

## Product wedge

Sell to teams that already have robots (warehouses, labs, logistics, integrators). They get value before we ever touch hardware. Our moat is workflow data, evaluation infrastructure, and integration quality.

## Folder layout

```
sim/          Simulation layer — MuJoCo environments, replay engine, scenario definitions
robot_api/    Robot data layer — log parsers, data schemas, connector stubs
backend/      FastAPI Python backend — REST API, job queue, metrics, auth
webapp/       React + Vite frontend — mission list, replay viewer, eval dashboard
evals/        Evaluation service — metrics, anomaly detection, report generation
infra/        Docker Compose, env templates, deployment config
scripts/      Reproducible demo and test scripts — every feature must have one
docs/         Architecture and API documentation
```

## Stack

- **Simulation**: MuJoCo (primary, lightweight, Mac-friendly); Isaac Sim later when NVIDIA acceleration is needed
- **Backend**: Python 3.13 + FastAPI + PostgreSQL + Redis (job queue)
- **Frontend**: React + Vite + TypeScript
- **AI**: Claude API via `anthropic` SDK (failure reasoning, policy comparison)
- **Infra**: Docker Compose for local dev; single VPS for early production

## Coding rules

1. **Every feature ends with a runnable script in `scripts/`** — if it can't be demoed from the CLI, it's not done.
2. **Never change public API interfaces without updating `evals/` tests** — sim and eval must stay in sync.
3. **Keep launch files runnable** — `docker compose up` must always work from a clean clone.
4. **Always log metrics** — every replay run writes structured JSON to the `runs/` output directory.
5. **Prefer reproducible scripts over ad hoc notebooks** — no notebooks in `sim/` or `evals/`.
6. **Do not add NVIDIA AI Enterprise or paid cloud before a customer forces it** — stay on open/free stack.
7. **Do not build a general platform** — every PR should map to one painful workflow a customer pays to fix.
8. **Auth is required on the backend from day one** — no unauthed endpoints except `/health`.

## Current milestone: Days 1–30

Narrow use case: **warehouse robot mission failure replay**.

- Input: robot trajectory log (JSON or ROS bag converted to JSON)
- Process: replay trajectory in MuJoCo, compute metrics (collision, deviation, timeout)
- Output: failure report with annotated replay, metric JSON, pass/fail verdict

MVP is done when a user can upload a log, see the replay, and download a report — without touching a terminal.

## What to postpone

- Custom hardware
- Humanoid robots as primary market
- NVIDIA AI Enterprise licensing
- Multi-robot fleet coordination (Open-RMF) before single-robot QA is working
- Foundation model training (Cosmos RL, GR00T) before product is validated

## gstack workflow

Use gstack slash commands for the development lifecycle:
- `/plan` before any non-trivial feature
- `/review` before merging
- `/qa` before shipping
- `/ship` to create PRs
