"""Source provenance and normalized location observations for imported jobs."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class JobSourceObservation(Base):
    __tablename__ = "job_source_observations"
    __table_args__ = (
        UniqueConstraint("artifact_sha256", "csv_record_number", name="uq_job_source_observations_physical_row"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    artifact_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    csv_record_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source_job_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    pipeline_version: Mapped[str] = mapped_column(String(128), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    pipeline_run_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)

    job: Mapped["Job | None"] = relationship(back_populates="source_observations")  # type: ignore[name-defined]


class JobLocationObservation(Base):
    __tablename__ = "job_location_observations"
    __table_args__ = (
        UniqueConstraint("job_id", "district", name="uq_job_location_observations_job_district"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(255), nullable=False)

    job: Mapped["Job"] = relationship(back_populates="location_observations")  # type: ignore[name-defined]