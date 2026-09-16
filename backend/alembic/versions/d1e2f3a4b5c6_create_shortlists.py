"""create shortlists table

Revision ID: d1e2f3a4b5c6
Revises: c9d0e1f2a3b4
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "shortlists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("match_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "candidate_id", name="uq_shortlists_job_candidate"),
    )
    op.create_index("ix_shortlists_candidate_id", "shortlists", ["candidate_id"], unique=False)
    op.create_index("ix_shortlists_job_id", "shortlists", ["job_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_shortlists_job_id", table_name="shortlists")
    op.drop_index("ix_shortlists_candidate_id", table_name="shortlists")
    op.drop_table("shortlists")
