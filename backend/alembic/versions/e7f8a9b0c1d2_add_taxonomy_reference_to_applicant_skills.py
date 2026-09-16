"""add taxonomy reference to applicant skills

Revision ID: e7f8a9b0c1d2
Revises: c6486a04695f
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, Sequence[str], None] = "c6486a04695f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add nullable taxonomy fields without inventing mappings for old rows."""
    op.add_column(
        "applicant_skills",
        sa.Column("skill_id", sa.String(length=10), nullable=True),
    )
    op.add_column(
        "applicant_skills",
        sa.Column("taxonomy_version", sa.String(length=32), nullable=True),
    )
    op.create_foreign_key(
        "fk_applicant_skills_skill_id_canonical_skills",
        "applicant_skills",
        "canonical_skills",
        ["skill_id"],
        ["skill_id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_applicant_skills_skill_id",
        "applicant_skills",
        ["skill_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_applicant_skills_skill_id", table_name="applicant_skills")
    op.drop_constraint(
        "fk_applicant_skills_skill_id_canonical_skills",
        "applicant_skills",
        type_="foreignkey",
    )
    op.drop_column("applicant_skills", "taxonomy_version")
    op.drop_column("applicant_skills", "skill_id")