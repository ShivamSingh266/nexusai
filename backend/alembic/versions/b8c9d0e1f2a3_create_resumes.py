"""create applicant resume metadata

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, Sequence[str], None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resumes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("applicant_id", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["applicant_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_resumes_applicant_id_users",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resumes_applicant_id", "resumes", ["applicant_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_resumes_applicant_id", table_name="resumes")
    op.drop_table("resumes")
