from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RoadmapStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    archived = "archived"


class RoadmapItemStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    skipped = "skipped"


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id: Mapped[int] = mapped_column(primary_key=True)
    applicant_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    taxonomy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[RoadmapStatus] = mapped_column(
        Enum(RoadmapStatus, name="roadmap_status"),
        nullable=False,
        default=RoadmapStatus.active,
        server_default=RoadmapStatus.active.value,
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

    items: Mapped[list["RoadmapItem"]] = relationship(
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="RoadmapItem.position",
    )

    applicant: Mapped["User"] = relationship(  # type: ignore[name-defined]
        back_populates="roadmaps",
    )


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"
    __table_args__ = (
        UniqueConstraint(
            "roadmap_id",
            "position",
            name="uq_roadmap_items_roadmap_position",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    roadmap_id: Mapped[int] = mapped_column(
        ForeignKey("roadmaps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[str] = mapped_column(
        String(10),
        ForeignKey(
            "canonical_skills.skill_id",
            ondelete="RESTRICT",
            name="fk_roadmap_items_skill_id_canonical_skills",
        ),
        nullable=False,
        index=True,
    )
    taxonomy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[RoadmapItemStatus] = mapped_column(
        Enum(RoadmapItemStatus, name="roadmap_item_status"),
        nullable=False,
        default=RoadmapItemStatus.pending,
        server_default=RoadmapItemStatus.pending.value,
    )
    course_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    resource_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    roadmap: Mapped[Roadmap] = relationship(back_populates="items")
