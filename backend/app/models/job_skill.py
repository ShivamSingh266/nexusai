"""Canonical skill requirements attached to a job posting."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class JobSkill(Base):
    __tablename__ = "job_skills"

    __table_args__ = (
        UniqueConstraint("job_id", "skill_id", name="uq_job_skills_job_skill"),
        CheckConstraint(
            "role_importance >= 0 AND role_importance <= 1",
            name="ck_job_skills_role_importance_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    skill_id: Mapped[str] = mapped_column(
        String(10),
        ForeignKey(
            "canonical_skills.skill_id",
            ondelete="RESTRICT",
            name="fk_job_skills_skill_id_canonical_skills",
        ),
        nullable=False,
        index=True,
    )

    taxonomy_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    role_importance: Mapped[float] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        default=1.0,
        server_default="1.0",
    )

    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
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

    job: Mapped["Job"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="job_skills",
    )

    canonical_skill: Mapped["CanonicalSkill"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="job_skills",
    )