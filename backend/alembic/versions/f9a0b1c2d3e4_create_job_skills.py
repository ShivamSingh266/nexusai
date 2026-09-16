"""create job skills

Revision ID: f9a0b1c2d3e4
Revises: e7f8a9b0c1d2
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f9a0b1c2d3e4"
down_revision: Union[str, Sequence[str], None] = "e7f8a9b0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_skills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.String(length=10), nullable=False),
        sa.Column("taxonomy_version", sa.String(length=32), nullable=False),
        sa.Column(
            "role_importance",
            sa.Numeric(precision=3, scale=2),
            server_default="1.0",
            nullable=False,
        ),
        sa.Column(
            "is_mandatory",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            ondelete="CASCADE",
            name="fk_job_skills_job_id_jobs",
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["canonical_skills.skill_id"],
            ondelete="RESTRICT",
            name="fk_job_skills_skill_id_canonical_skills",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "skill_id", name="uq_job_skills_job_skill"),
        sa.CheckConstraint(
            "role_importance >= 0 AND role_importance <= 1",
            name="ck_job_skills_role_importance_range",
        ),
    )
    op.create_index("ix_job_skills_job_id", "job_skills", ["job_id"], unique=False)
    op.create_index("ix_job_skills_skill_id", "job_skills", ["skill_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_job_skills_skill_id", table_name="job_skills")
    op.drop_index("ix_job_skills_job_id", table_name="job_skills")
    op.drop_table("job_skills")