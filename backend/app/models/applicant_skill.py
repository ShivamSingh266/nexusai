from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ApplicantSkill(Base):
    __tablename__ = "applicant_skills"

    # Composite uniqueness: one skill_name per user (case-sensitive at DB level;
    # case-insensitive protection is retained in the API layer via ilike).
    __table_args__ = (
        UniqueConstraint("user_id", "skill_name", name="uq_applicant_skills_user_skill"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    skill_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    proficiency_level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="beginner",
        server_default="beginner",
    )

    years_experience: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="applicant_skills",
    )