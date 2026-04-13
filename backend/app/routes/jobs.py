"""Job routes — track async replay and eval jobs."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()


class Job(BaseModel):
    id: str
    mission_id: str
    type: str  # replay | eval | report
    status: str  # queued | running | completed | failed
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


@router.get("/", response_model=list[Job])
async def list_jobs():
    # TODO: fetch from database
    return []


@router.get("/{job_id}", response_model=Job)
async def get_job(job_id: str):
    # TODO: fetch from database
    raise HTTPException(404, "Job not found")
