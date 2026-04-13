from sqlalchemy import String, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
import uuid


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id: Mapped[str] = mapped_column(String, ForeignKey("missions.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False)  # replay|eval|report
    status: Mapped[str] = mapped_column(String, default="queued")  # queued|running|completed|failed
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
