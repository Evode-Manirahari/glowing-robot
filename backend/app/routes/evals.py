"""Eval routes — metrics, reports, policy comparisons."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class EvalReport(BaseModel):
    mission_id: str
    verdict: str  # pass | fail | warning
    collision_count: int
    max_deviation_m: float
    completion_rate: float
    duration_s: float
    anomalies: list[str]
    ai_summary: Optional[str] = None


@router.get("/{mission_id}/report", response_model=EvalReport)
async def get_eval_report(mission_id: str):
    # TODO: fetch from database
    raise HTTPException(404, "Eval report not found")


@router.post("/{mission_id}/summarize")
async def summarize_with_ai(mission_id: str):
    """Use Claude to generate a natural-language failure summary."""
    # TODO: load eval metrics, call Claude API, store and return summary
    raise HTTPException(501, "Not yet implemented")
