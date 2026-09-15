"""Canonical skill taxonomy models.

Architecture boundaries:
  - CanonicalSkill is the shared, M4-owned taxonomy entity.
  - SkillAlias provides alternate textual forms for a canonical skill.
  - Neither ApplicantSkill nor Job reference these tables yet.
    ApplicantSkill → CanonicalSkill FK and JobSkill are future tasks.

Deletion behaviour:
  - SkillAlias.skill_id uses ON DELETE RESTRICT intentionally.
    A canonical skill cannot be removed while aliases still reference it.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CanonicalSkill(Base):
    """Canonical skill as defined by the NexusAI taxonomy (sourced from ESCO).

    The primary key ``skill_id`` is a human-readable opaque identifier of the
    form ``SKILL_XXXX`` (e.g. ``SKILL_0001``). IDs are assigned by Member 4's
    ingestion pipeline and must NEVER be renumbered or regenerated here.
    """

    __tablename__ = "canonical_skills"

    __table_args__ = (
        # UNIQUE on normalized_name is safe for this dataset.
        UniqueConstraint(
            "normalized_name",
            name="uq_canonical_skills_normalized_name",
        ),

        # Index on category to support the category filter in search.
        Index(
            "ix_canonical_skills_category",
            "category",
        ),
    )

    skill_id: Mapped[str] = mapped_column(
        String(10),
        primary_key=True,
        nullable=False,
    )

    canonical_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    normalized_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="ESCO",
        server_default="ESCO",
    )

    taxonomy_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    esco_uri: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
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

    aliases: Mapped[list["SkillAlias"]] = relationship(
        back_populates="canonical_skill",
        cascade="save-update, merge",
        passive_deletes=True,
    )


class SkillAlias(Base):
    """An alternate textual form for a canonical skill.

    One alias may legitimately map to more than one canonical skill.
    Therefore ``normalized_alias`` is NOT globally unique; uniqueness is
    enforced only as a composite UNIQUE(normalized_alias, skill_id).
    """

    __tablename__ = "skill_aliases"

    __table_args__ = (
        UniqueConstraint(
            "normalized_alias",
            "skill_id",
            name="uq_skill_aliases_normalized_alias_skill",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_skill_aliases_confidence_range",
        ),
        Index(
            "ix_skill_aliases_skill_id",
            "skill_id",
        ),
    )

    # BIGINT in PostgreSQL, INTEGER in SQLite.
    # SQLite requires INTEGER for automatic primary-key generation.
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )

    alias: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    normalized_alias: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    skill_id: Mapped[str] = mapped_column(
        String(10),
        ForeignKey(
            "canonical_skills.skill_id",
            ondelete="RESTRICT",
            name="fk_skill_aliases_skill_id_canonical_skills",
        ),
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        default=0.90,
        server_default="0.90",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    canonical_skill: Mapped["CanonicalSkill"] = relationship(
        back_populates="aliases",
    )