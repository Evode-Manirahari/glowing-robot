from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.eval_report import EvalReport
from app.models.mission import Mission
from app.models.user import User
from app.services.auth import get_current_user
from app.services import eval_service

router = APIRouter()


class EvalReportOut(BaseModel):
    mission_id: str
    verdict: str
    collision_count: int
    max_deviation_m: float
    completion_rate: float
    duration_s: float
    frame_count: int
    anomalies: list[str]
    ai_summary: Optional[str] = None

    class Config:
        from_attributes = True


async def _get_report_for_user(mission_id: str, user: User, db: AsyncSession) -> EvalReport:
    # Verify mission belongs to user
    m = await db.execute(
        select(Mission).where(Mission.id == mission_id, Mission.user_id == user.id)
    )
    if not m.scalar_one_or_none():
        raise HTTPException(404, "Mission not found")

    r = await db.execute(select(EvalReport).where(EvalReport.mission_id == mission_id))
    report = r.scalar_one_or_none()
    if not report:
        raise HTTPException(404, "Eval report not ready yet")
    return report


@router.get("/{mission_id}/report", response_model=EvalReportOut)
async def get_eval_report(
    mission_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await _get_report_for_user(mission_id, user, db)


@router.post("/{mission_id}/summarize")
async def summarize_with_ai(
    mission_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Re-generate AI summary for a mission (async)."""
    report = await _get_report_for_user(mission_id, user, db)

    async def _do_summarize() -> None:
        metrics = {
            "verdict": report.verdict,
            "collision_count": report.collision_count,
            "max_deviation_m": report.max_deviation_m,
            "completion_rate": report.completion_rate,
            "duration_s": report.duration_s,
            "frame_count": report.frame_count,
            "anomalies": report.anomalies,
        }
        summary = await eval_service.generate_ai_summary(metrics)
        async with __import__("app.database", fromlist=["AsyncSessionLocal"]).AsyncSessionLocal() as s:
            r2 = await s.execute(select(EvalReport).where(EvalReport.mission_id == mission_id))
            rpt = r2.scalar_one()
            rpt.ai_summary = summary
            await s.commit()

    background_tasks.add_task(_do_summarize)
    return {"message": "AI summary generation started"}
