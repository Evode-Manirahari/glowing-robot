from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import missions, jobs, evals, health

app = FastAPI(
    title="glowing-robot",
    description="Robot QA and validation platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(missions.router, prefix="/missions", tags=["missions"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(evals.router, prefix="/evals", tags=["evals"])
