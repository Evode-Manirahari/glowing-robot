from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.database import get_db
from app.models.mission import Mission
from app.models.job import Job
from app.models.eval_report import EvalReport
from app.models.user import User
from app.services.auth import get_current_user
from app.services import storage, job_runner
import uuid
import json

router = APIRouter()


class MissionOut(BaseModel):
    id: str
    name: str
    robot_type: str
    uploaded_at: datetime
    status: str
    log_filename: str
    verdict: Optional[str] = None

    class Config:
        from_attributes = True


class MissionUploadResponse(BaseModel):
    mission_id: str
    job_id: str
    message: str


@router.get("/", response_model=list[MissionOut])
async def list_missions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(50, le=200),
    verdict: Optional[str] = Query(None, description="Filter by verdict: pass|fail|warning"),
    q: Optional[str] = Query(None, description="Search by mission name"),
):
    stmt = select(Mission).where(Mission.user_id == user.id)
    if verdict:
        stmt = stmt.where(Mission.verdict == verdict)
    if q:
        stmt = stmt.where(Mission.name.ilike(f"%{q}%"))
    stmt = stmt.order_by(Mission.uploaded_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/upload", response_model=MissionUploadResponse, status_code=202)
async def upload_mission(
    background_tasks: BackgroundTasks,
    name: str,
    robot_type: str,
    log_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not log_file.filename.endswith((".json", ".csv")):
        raise HTTPException(400, "Log must be .json or .csv")
    if log_file.size and log_file.size > 50 * 1024 * 1024:  # 50 MB limit
        raise HTTPException(413, "Log file too large (max 50 MB)")

    mission_id = str(uuid.uuid4())
    log_path = await storage.save_log(mission_id, log_file)

    mission = Mission(
        id=mission_id,
        user_id=user.id,
        name=name,
        robot_type=robot_type,
        log_filename=log_file.filename,
        log_path=str(log_path),
        status="pending",
    )
    db.add(mission)
    await db.commit()  # commit mission first so the FK constraint on jobs is satisfied

    job_id = str(uuid.uuid4())
    job = Job(id=job_id, mission_id=mission_id, type="replay", status="queued")
    db.add(job)
    await db.commit()

    background_tasks.add_task(job_runner.run_job, job_id)

    return MissionUploadResponse(
        mission_id=mission_id,
        job_id=job_id,
        message="Mission uploaded. Replay and evaluation started.",
    )


@router.get("/{mission_id}", response_model=MissionOut)
async def get_mission(
    mission_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Mission).where(Mission.id == mission_id, Mission.user_id == user.id)
    )
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(404, "Mission not found")
    return mission


@router.get("/{mission_id}/replay")
async def get_replay_data(
    mission_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return frame-by-frame trajectory for the frontend viewer."""
    # Verify ownership
    m_result = await db.execute(
        select(Mission).where(Mission.id == mission_id, Mission.user_id == user.id)
    )
    if not m_result.scalar_one_or_none():
        raise HTTPException(404, "Mission not found")

    r_result = await db.execute(
        select(EvalReport).where(EvalReport.mission_id == mission_id)
    )
    report = r_result.scalar_one_or_none()
    if not report or not report.replay_frames:
        raise HTTPException(404, "Replay data not yet available")

    return {
        "frames": report.replay_frames,
        "waypoints": report.waypoints or [],
        "obstacles": report.obstacles or [],
        "collision_times": report.collision_times or [],
    }


@router.get("/{mission_id}/report/download")
async def download_report(
    mission_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Download the full eval report as a JSON file."""
    m_result = await db.execute(
        select(Mission).where(Mission.id == mission_id, Mission.user_id == user.id)
    )
    mission = m_result.scalar_one_or_none()
    if not mission:
        raise HTTPException(404, "Mission not found")

    r_result = await db.execute(select(EvalReport).where(EvalReport.mission_id == mission_id))
    report = r_result.scalar_one_or_none()
    if not report:
        raise HTTPException(404, "Report not ready yet")

    payload = {
        "schema_version": "1.0",
        "mission": {
            "id": mission.id,
            "name": mission.name,
            "robot_type": mission.robot_type,
            "uploaded_at": mission.uploaded_at.isoformat(),
            "log_filename": mission.log_filename,
        },
        "verdict": report.verdict,
        "metrics": {
            "collision_count": report.collision_count,
            "max_deviation_m": report.max_deviation_m,
            "completion_rate": report.completion_rate,
            "duration_s": report.duration_s,
            "frame_count": report.frame_count,
        },
        "anomalies": report.anomalies,
        "ai_summary": report.ai_summary,
    }
    filename = f"report_{mission.name[:40].replace(' ', '_')}_{mission_id[:8]}.json"
    return Response(
        content=json.dumps(payload, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{mission_id}", status_code=204)
async def delete_mission(
    mission_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Mission).where(Mission.id == mission_id, Mission.user_id == user.id)
    )
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(404, "Mission not found")
    await db.delete(mission)
    await db.commit()
