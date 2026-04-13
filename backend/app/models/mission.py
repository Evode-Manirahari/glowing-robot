from sqlalchemy import String, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
import uuid


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    robot_type: Mapped[str] = mapped_column(String, nullable=False)
    log_filename: Mapped[str] = mapped_column(String, nullable=False)
    log_path: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|replaying|evaluated|failed
    verdict: Mapped[str | None] = mapped_column(String, nullable=True)
    uploaded_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
