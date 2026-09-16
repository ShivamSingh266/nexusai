"""Job model and its relationship to canonical skill requirements."""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class JobStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    closed = "closed"


class EmploymentType(str, enum.Enum):
    full_time = "full_time"
    part_time = "part_time"
    contract = "contract"
    internship = "internship"
    freelance = "freelance"


class WorkMode(str, enum.Enum):
    onsite = "onsite"
    remote = "remote"
    hybrid = "hybrid"


class Job(Base):
    __tablename__ = "jobs"

    # Indexes that support the query patterns used by the listing endpoint
    __table_args__ = (
        # Recruiter views filtered by company + status
        Index("ix_jobs_company_status", "company_id", "status"),
        UniqueConstraint("source", "source_job_id", name="uq_jobs_source_source_job_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # ------------------------------------------------------------------ #
    # Owning company                                                        #
    # ------------------------------------------------------------------ #
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------ #
    # Core fields                                                           #
    # ------------------------------------------------------------------ #
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source_job_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    posting_time_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    posted_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    anticipated_start_min: Mapped[str | None] = mapped_column(String(50), nullable=True)
    anticipated_start_max: Mapped[str | None] = mapped_column(String(50), nullable=True)

    sector: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    employment_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    work_mode: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # Experience & education                                                #
    # ------------------------------------------------------------------ #
    experience_min: Mapped[float | None] = mapped_column(
        Numeric(4, 1),
        nullable=True,
    )

    experience_max: Mapped[float | None] = mapped_column(
        Numeric(4, 1),
        nullable=True,
    )

    education_requirement: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # Compensation                                                          #
    # ------------------------------------------------------------------ #
    salary_min: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    salary_max: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    # ------------------------------------------------------------------ #
    # Lifecycle                                                             #
    # ------------------------------------------------------------------ #
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=JobStatus.draft.value,
        server_default=JobStatus.draft.value,
        index=True,
    )

    # ------------------------------------------------------------------ #
    # Audit timestamps                                                      #
    # ------------------------------------------------------------------ #
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

    # ------------------------------------------------------------------ #
    # Relationships                                                         #
    # ------------------------------------------------------------------ #
    company: Mapped["Company"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="jobs",
    )

    job_skills: Mapped[list["JobSkill"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    source_observations: Mapped[list["JobSourceObservation"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    location_observations: Mapped[list["JobLocationObservation"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def districts(self) -> list[str]:
        """Return normalized imported districts without changing legacy location."""
        return sorted(
            (observation.district for observation in self.location_observations),
            key=str.casefold,
        )

    shortlists: Mapped[list["Shortlist"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
