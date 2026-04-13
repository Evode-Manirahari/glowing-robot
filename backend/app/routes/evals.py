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
    collision_times: list[float] = []
    ai_summary: Optional[str] = None

    class Config:
        from_attributes = True


class CompareResponse(BaseModel):
    report_a: EvalReportOut
    report_b: EvalReportOut
    mission_a_name: str
    mission_b_name: str
    comparison_summary: str


async def _get_report_for_user(mission_id: str, user: User, db: AsyncSession) -> EvalReport:
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


@router.get("/compare", response_model=CompareResponse)
async def compare_missions(
    mission_a: str,
    mission_b: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Compare two missions side by side with an AI-generated analysis."""
    if mission_a == mission_b:
        raise HTTPException(400, "Select two different missions to compare")

    report_a = await _get_report_for_user(mission_a, user, db)
    report_b = await _get_report_for_user(mission_b, user, db)

    # Fetch mission names for the summary
    ma = await db.execute(select(Mission).where(Mission.id == mission_a))
    mb = await db.execute(select(Mission).where(Mission.id == mission_b))
    name_a = ma.scalar_one().name
    name_b = mb.scalar_one().name

    comparison_summary = await eval_service.generate_comparison_summary(
        report_a={
            "verdict": report_a.verdict,
            "collision_count": report_a.collision_count,
            "max_deviation_m": report_a.max_deviation_m,
            "completion_rate": report_a.completion_rate,
            "duration_s": report_a.duration_s,
            "anomalies": report_a.anomalies,
        },
        name_a=name_a,
        report_b={
            "verdict": report_b.verdict,
            "collision_count": report_b.collision_count,
            "max_deviation_m": report_b.max_deviation_m,
            "completion_rate": report_b.completion_rate,
            "duration_s": report_b.duration_s,
            "anomalies": report_b.anomalies,
        },
        name_b=name_b,
    )

    return CompareResponse(
        report_a=EvalReportOut.model_validate(report_a),
        report_b=EvalReportOut.model_validate(report_b),
        mission_a_name=name_a,
        mission_b_name=name_b,
        comparison_summary=comparison_summary,
    )


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
