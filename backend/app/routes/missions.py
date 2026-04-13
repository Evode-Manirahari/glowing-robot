"""Mission routes — upload logs, list missions, get replay data."""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

router = APIRouter()


class Mission(BaseModel):
    id: str
    name: str
    robot_type: str
    uploaded_at: datetime
    status: str  # pending | replaying | evaluated | failed
    log_filename: str
    verdict: Optional[str] = None  # pass | fail | warning


class MissionUploadResponse(BaseModel):
    mission_id: str
    message: str


@router.get("/", response_model=list[Mission])
async def list_missions():
    # TODO: fetch from database
    return []


@router.post("/upload", response_model=MissionUploadResponse)
async def upload_mission(
    name: str,
    robot_type: str,
    log_file: UploadFile = File(...),
):
    if not log_file.filename.endswith((".json", ".csv", ".bag.json")):
        raise HTTPException(400, "Log must be .json, .csv, or .bag.json")

    mission_id = str(uuid.uuid4())
    # TODO: persist log file and enqueue replay job
    return MissionUploadResponse(
        mission_id=mission_id,
        message="Mission uploaded. Replay job enqueued.",
    )


@router.get("/{mission_id}", response_model=Mission)
async def get_mission(mission_id: str):
    # TODO: fetch from database
    raise HTTPException(404, "Mission not found")


@router.get("/{mission_id}/replay")
async def get_replay_data(mission_id: str):
    """Return frame-by-frame trajectory for the frontend viewer."""
    # TODO: load from stored replay output
    raise HTTPException(404, "Replay data not found")
