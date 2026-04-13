from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import create_tables
from app.routes import missions, jobs, evals, health, auth

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title="glowing-robot",
    description="Robot QA and validation platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(missions.router, prefix="/missions", tags=["missions"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(evals.router, prefix="/evals", tags=["evals"])
