import json
import shutil
from pathlib import Path
from fastapi import UploadFile
from app.config import get_settings

settings = get_settings()


def _upload_path(mission_id: str) -> Path:
    d = Path(settings.upload_dir) / mission_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _runs_path(mission_id: str) -> Path:
    d = Path(settings.runs_dir) / mission_id
    d.mkdir(parents=True, exist_ok=True)
    return d


async def save_log(mission_id: str, file: UploadFile) -> Path:
    dest = _upload_path(mission_id) / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return dest


def load_log(log_path: str) -> dict:
    with open(log_path) as f:
        return json.load(f)


def save_report(mission_id: str, report: dict) -> Path:
    dest = _runs_path(mission_id) / "report.json"
    with open(dest, "w") as f:
        json.dump(report, f, indent=2)
    return dest


def load_report(mission_id: str) -> dict | None:
    path = Path(settings.runs_dir) / mission_id / "report.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)
