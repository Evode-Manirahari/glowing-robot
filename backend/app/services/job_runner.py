"""
Job runner — executes replay + eval jobs as FastAPI background tasks.
Uses AsyncSessionLocal directly (not injected) since it runs outside a request context.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models.job import Job
from app.models.mission import Mission
from app.models.eval_report import EvalReport
from app.services import eval_service, storage

logger = logging.getLogger(__name__)


async def run_job(job_id: str) -> None:
    async with AsyncSessionLocal() as db:
        # Mark job as running
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if job is None:
            logger.error(f"Job {job_id} not found")
            return

        job.status = "running"
        await db.commit()

        try:
            await _execute_job(db, job)
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
        except Exception as exc:
            logger.exception(f"Job {job_id} failed: {exc}")
            job.status = "failed"
            job.error = str(exc)
            job.completed_at = datetime.now(timezone.utc)

            # Mark mission as failed
            await db.execute(
                update(Mission).where(Mission.id == job.mission_id).values(status="failed")
            )

        await db.commit()


async def _execute_job(db, job: Job) -> None:
    # Load mission
    result = await db.execute(select(Mission).where(Mission.id == job.mission_id))
    mission = result.scalar_one()

    if job.type == "replay":
        await _run_replay_and_eval(db, mission)


async def _run_replay_and_eval(db, mission: Mission) -> None:
    # Mark mission as replaying
    mission.status = "replaying"
    await db.commit()

    # Run replay + compute metrics
    metrics = eval_service.run_replay(mission.log_path)

    # Generate AI summary
    ai_summary = await eval_service.generate_ai_summary(metrics)

    # Persist eval report
    report = EvalReport(
        mission_id=mission.id,
        verdict=metrics["verdict"],
        collision_count=metrics["collision_count"],
        max_deviation_m=metrics["max_deviation_m"],
        completion_rate=metrics["completion_rate"],
        duration_s=metrics["duration_s"],
        frame_count=metrics["frame_count"],
        anomalies=metrics["anomalies"],
        replay_frames=metrics["replay_frames"],
        waypoints=metrics.get("waypoints", []),
        obstacles=metrics.get("obstacles", []),
        collision_times=metrics.get("collision_times", []),
        ai_summary=ai_summary,
    )
    db.add(report)

    # Save JSON report to disk
    storage.save_report(mission.id, {**metrics, "ai_summary": ai_summary})

    # Update mission status and verdict
    mission.status = "evaluated"
    mission.verdict = metrics["verdict"]
    await db.commit()
