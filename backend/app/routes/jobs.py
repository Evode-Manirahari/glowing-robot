from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.job import Job
from app.models.mission import Mission
from app.models.user import User
from app.services.auth import get_current_user

router = APIRouter()


class JobOut(BaseModel):
    id: str
    mission_id: str
    type: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/", response_model=list[JobOut])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Only return jobs for this user's missions
    result = await db.execute(
        select(Job)
        .join(Mission, Job.mission_id == Mission.id)
        .where(Mission.user_id == user.id)
        .order_by(Job.created_at.desc())
        .limit(100)
    )
    return result.scalars().all()


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Job)
        .join(Mission, Job.mission_id == Mission.id)
        .where(Job.id == job_id, Mission.user_id == user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    return job
