from sqlalchemy import String, DateTime, ForeignKey, func, Float, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
import uuid


class EvalReport(Base):
    __tablename__ = "eval_reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id: Mapped[str] = mapped_column(String, ForeignKey("missions.id"), nullable=False, unique=True, index=True)
    verdict: Mapped[str] = mapped_column(String, nullable=False)  # pass|fail|warning
    collision_count: Mapped[int] = mapped_column(Integer, default=0)
    max_deviation_m: Mapped[float] = mapped_column(Float, default=0.0)
    completion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    duration_s: Mapped[float] = mapped_column(Float, default=0.0)
    frame_count: Mapped[int] = mapped_column(Integer, default=0)
    anomalies: Mapped[list] = mapped_column(JSON, default=list)
    replay_frames: Mapped[list | None] = mapped_column(JSON, nullable=True)  # for frontend viewer
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
