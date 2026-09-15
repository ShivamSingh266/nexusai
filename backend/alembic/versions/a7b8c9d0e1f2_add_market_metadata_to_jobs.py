"""add market source metadata to jobs

Revision ID: a7b8c9d0e1f2
Revises: f9a0b1c2d3e4
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f9a0b1c2d3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("source_job_id", sa.String(length=64), nullable=True))
    op.add_column("jobs", sa.Column("source", sa.String(length=64), nullable=True))
    op.add_column("jobs", sa.Column("sector", sa.String(length=100), nullable=True))
    op.create_index("ix_jobs_source_job_id", "jobs", ["source_job_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_jobs_source_job_id", table_name="jobs")
    op.drop_column("jobs", "sector")
    op.drop_column("jobs", "source")
    op.drop_column("jobs", "source_job_id")