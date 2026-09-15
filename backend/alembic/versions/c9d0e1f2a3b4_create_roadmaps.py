"""create applicant roadmaps

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roadmaps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("applicant_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("taxonomy_version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.Enum("active", "completed", "archived", name="roadmap_status"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["applicant_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_roadmaps_applicant_id", "roadmaps", ["applicant_id"], unique=False)
    op.create_table(
        "roadmap_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("roadmap_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.String(length=10), nullable=False),
        sa.Column("taxonomy_version", sa.String(length=32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("pending", "in_progress", "completed", "skipped", name="roadmap_item_status"), nullable=False),
        sa.Column("course_id", sa.String(length=64), nullable=True),
        sa.Column("resource_url", sa.String(length=2048), nullable=True),
        sa.Column("resource_title", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["roadmap_id"], ["roadmaps.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["canonical_skills.skill_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("roadmap_id", "position", name="uq_roadmap_items_roadmap_position"),
    )
    op.create_index("ix_roadmap_items_roadmap_id", "roadmap_items", ["roadmap_id"], unique=False)
    op.create_index("ix_roadmap_items_skill_id", "roadmap_items", ["skill_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_roadmap_items_skill_id", table_name="roadmap_items")
    op.drop_index("ix_roadmap_items_roadmap_id", table_name="roadmap_items")
    op.drop_table("roadmap_items")
    op.drop_index("ix_roadmaps_applicant_id", table_name="roadmaps")
    op.drop_table("roadmaps")
    sa.Enum(name="roadmap_item_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="roadmap_status").drop(op.get_bind(), checkfirst=True)
