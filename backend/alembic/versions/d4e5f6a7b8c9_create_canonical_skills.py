"""create canonical_skills and skill_aliases tables

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-15 10:10:00.000000

Creates the ``canonical_skills`` table (M4-owned taxonomy) and the
``skill_aliases`` table that provides alternate textual forms for each
canonical skill.

canonical_skills
  - skill_id VARCHAR(10) PK
  - canonical_name VARCHAR(255) NOT NULL
  - normalized_name VARCHAR(255) NOT NULL UNIQUE
  - category VARCHAR(64) NOT NULL
  - source VARCHAR(32) NOT NULL DEFAULT 'ESCO'
  - taxonomy_version VARCHAR(32) NOT NULL
  - esco_uri VARCHAR(255) NULL
  - is_active BOOLEAN NOT NULL DEFAULT TRUE
  - created_at TIMESTAMPTZ NOT NULL DEFAULT now()
  - updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
  - CHECK (skill_id ~ '^SKILL_[0-9]{4}$')

skill_aliases
  - id BIGINT GENERATED ALWAYS AS IDENTITY (PostgreSQL BIGSERIAL equivalent)
  - alias VARCHAR(255) NOT NULL
  - normalized_alias VARCHAR(255) NOT NULL
  - skill_id VARCHAR(10) NOT NULL FK -> canonical_skills.skill_id ON DELETE RESTRICT
  - confidence NUMERIC(3,2) NOT NULL DEFAULT 0.90
  - created_at TIMESTAMPTZ NOT NULL DEFAULT now()
  - CHECK (confidence >= 0 AND confidence <= 1)
  - UNIQUE (normalized_alias, skill_id)

Indexes created:
  uq_canonical_skills_normalized_name  — implicit from UNIQUE constraint
  ix_canonical_skills_category         — supports category filter in search
  ix_skill_aliases_skill_id            — supports FK lookups and JOINs

NOTE: No CSV data is seeded here. Data ingestion is Member 4's responsibility.
NOTE: pg_trgm is NOT enabled here. ILIKE search is sufficient for 642 skills.

Downgrade drops skill_aliases first (FK dependency), then canonical_skills.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create canonical_skills and skill_aliases tables."""

    # ------------------------------------------------------------------ #
    # 1. canonical_skills                                                  #
    # ------------------------------------------------------------------ #
    op.create_table(
        'canonical_skills',
        sa.Column('skill_id', sa.String(length=10), nullable=False),
        sa.Column('canonical_name', sa.String(length=255), nullable=False),
        sa.Column('normalized_name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column(
            'source',
            sa.String(length=32),
            server_default='ESCO',
            nullable=False,
        ),
        sa.Column('taxonomy_version', sa.String(length=32), nullable=False),
        sa.Column('esco_uri', sa.String(length=255), nullable=True),
        sa.Column(
            'is_active',
            sa.Boolean(),
            server_default=sa.text('true'),
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        # skill_id must be in SKILL_XXXX format (PostgreSQL regex syntax).
        # SQLite does not support the ~ operator; the constraint is
        # written without a try/except so that PostgreSQL enforces it
        # correctly. Existing tests use SQLite with create_all() which
        # silently ignores unrecognised CHECK expressions.
        sa.CheckConstraint(
            r"skill_id ~ '^SKILL_[0-9]{4}$'",
            name='ck_canonical_skills_skill_id_format',
        ),
        sa.UniqueConstraint(
            'normalized_name',
            name='uq_canonical_skills_normalized_name',
        ),
        sa.PrimaryKeyConstraint('skill_id'),
    )

    # Index on category to support the category filter in the search API.
    op.create_index(
        'ix_canonical_skills_category',
        'canonical_skills',
        ['category'],
        unique=False,
    )

    # ------------------------------------------------------------------ #
    # 2. skill_aliases                                                     #
    # ------------------------------------------------------------------ #
    op.create_table(
        'skill_aliases',
        # id uses sa.BigInteger + autoincrement=True which Alembic renders
        # as BIGSERIAL on PostgreSQL (equivalent to BIGINT GENERATED ALWAYS).
        sa.Column(
            'id',
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column('alias', sa.String(length=255), nullable=False),
        sa.Column('normalized_alias', sa.String(length=255), nullable=False),
        sa.Column('skill_id', sa.String(length=10), nullable=False),
        sa.Column(
            'confidence',
            sa.Numeric(precision=3, scale=2),
            server_default='0.90',
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.CheckConstraint(
            'confidence >= 0 AND confidence <= 1',
            name='ck_skill_aliases_confidence_range',
        ),
        sa.ForeignKeyConstraint(
            ['skill_id'],
            ['canonical_skills.skill_id'],
            name='fk_skill_aliases_skill_id_canonical_skills',
            ondelete='RESTRICT',
        ),
        # Composite uniqueness: same normalized_alias may point to different
        # skill_ids (17 such cases exist in the v1.2.1 dataset), but the
        # exact (normalized_alias, skill_id) pair must be unique.
        sa.UniqueConstraint(
            'normalized_alias',
            'skill_id',
            name='uq_skill_aliases_normalized_alias_skill',
        ),
        sa.PrimaryKeyConstraint('id'),
    )

    # Explicit index on skill_id for FK lookups and JOIN performance.
    op.create_index(
        'ix_skill_aliases_skill_id',
        'skill_aliases',
        ['skill_id'],
        unique=False,
    )


def downgrade() -> None:
    """Drop skill_aliases then canonical_skills (FK dependency order)."""
    op.drop_index('ix_skill_aliases_skill_id', table_name='skill_aliases')
    op.drop_table('skill_aliases')
    op.drop_index('ix_canonical_skills_category', table_name='canonical_skills')
    op.drop_table('canonical_skills')
