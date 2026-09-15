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
    form ``SKILL_XXXX`` (e.g. ``SKILL_0001``).  IDs are assigned by Member 4's
    ingestion pipeline and must NEVER be renumbered or regenerated here.
    """

    __tablename__ = "canonical_skills"

    __table_args__ = (
        # Enforce the SKILL_XXXX format at the database level.
        # SQLite does not enforce CHECK constraints by default; the migration
        # applies this only on PostgreSQL.
        CheckConstraint(
            r"skill_id ~ '^SKILL_[0-9]{4}$'",
            name="ck_canonical_skills_skill_id_format",
        ),
        # UNIQUE on normalized_name is safe for this dataset (verified: 0 dups).
        UniqueConstraint("normalized_name", name="uq_canonical_skills_normalized_name"),
        # Index on category to support the category filter in search.
        Index("ix_canonical_skills_category", "category"),
    )

    # ---------------------------------------------------------------------- #
    # Primary key                                                              #
    # ---------------------------------------------------------------------- #
    skill_id: Mapped[str] = mapped_column(
        String(10),
        primary_key=True,
        nullable=False,
    )

    # ---------------------------------------------------------------------- #
    # Core taxonomy fields                                                     #
    # ---------------------------------------------------------------------- #
    canonical_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    normalized_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        # UniqueConstraint defined in __table_args__; index is created
        # implicitly by the UNIQUE constraint itself.
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

    # ---------------------------------------------------------------------- #
    # Status                                                                   #
    # ---------------------------------------------------------------------- #
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # ---------------------------------------------------------------------- #
    # Audit timestamps                                                         #
    # ---------------------------------------------------------------------- #
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

    # ---------------------------------------------------------------------- #
    # Relationships                                                            #
    # ---------------------------------------------------------------------- #
    aliases: Mapped[list["SkillAlias"]] = relationship(
        back_populates="canonical_skill",
        cascade="save-update, merge",
        # Do NOT cascade delete — ON DELETE RESTRICT is enforced at DB level.
        passive_deletes=True,
    )


class SkillAlias(Base):
    """An alternate textual form (alias) for a :class:`CanonicalSkill`.

    One alias may legitimately map to more than one canonical skill (17 such
    cases confirmed in the v1.2.1 dataset).  Therefore ``normalized_alias`` is
    NOT globally unique; uniqueness is enforced only as a composite
    ``UNIQUE(normalized_alias, skill_id)`` to prevent exact duplicate
    alias-to-skill pairs.
    """

    __tablename__ = "skill_aliases"

    __table_args__ = (
        # Prevent the exact same (normalized_alias, skill_id) pair appearing twice.
        # Allows the same normalized_alias to point to different skill_ids.
        UniqueConstraint(
            "normalized_alias",
            "skill_id",
            name="uq_skill_aliases_normalized_alias_skill",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_skill_aliases_confidence_range",
        ),
        # Explicit index on skill_id for FK-lookups and join performance.
        Index("ix_skill_aliases_skill_id", "skill_id"),
    )

    # ---------------------------------------------------------------------- #
    # Primary key — BIGINT (maps to BIGSERIAL / identity on PostgreSQL)       #
    # ---------------------------------------------------------------------- #
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # ---------------------------------------------------------------------- #
    # Alias fields                                                             #
    # ---------------------------------------------------------------------- #
    alias: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    normalized_alias: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        # NOT globally unique — see __table_args__ for composite uniqueness.
    )

    # ---------------------------------------------------------------------- #
    # Foreign key                                                              #
    # ---------------------------------------------------------------------- #
    skill_id: Mapped[str] = mapped_column(
        String(10),
        ForeignKey(
            "canonical_skills.skill_id",
            ondelete="RESTRICT",
            name="fk_skill_aliases_skill_id_canonical_skills",
        ),
        nullable=False,
    )

    # ---------------------------------------------------------------------- #
    # Confidence score                                                         #
    # ---------------------------------------------------------------------- #
    confidence: Mapped[float] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        default=0.90,
        server_default="0.90",
    )

    # ---------------------------------------------------------------------- #
    # Audit timestamp (created only — aliases are immutable once inserted)    #
    # ---------------------------------------------------------------------- #
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ---------------------------------------------------------------------- #
    # Relationships                                                            #
    # ---------------------------------------------------------------------- #
    canonical_skill: Mapped["CanonicalSkill"] = relationship(
        back_populates="aliases",
    )
