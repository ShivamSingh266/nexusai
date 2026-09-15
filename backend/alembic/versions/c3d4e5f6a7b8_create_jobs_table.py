"""create jobs table

Revision ID: c3d4e5f6a7b8
Revises: b7e8f9a0b1c2
Create Date: 2026-09-15 02:00:00.000000

Creates the `jobs` table with all core fields for the NexusAI job management
module.  No skill references are included here — JobSkill will be added in a
future migration once Member 4's canonical_skills table is finalised.

Indexes created:
  ix_jobs_company_id        — fast lookup of all jobs for a company
  ix_jobs_status            — fast published-only filtering for applicants
  ix_jobs_company_status    — combined filter for recruiter listing
  ix_jobs_title             — supports title search queries
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b7e8f9a0b1c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — create jobs table."""
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('employment_type', sa.String(length=50), nullable=True),
        sa.Column('work_mode', sa.String(length=50), nullable=True),
        sa.Column('experience_min', sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column('experience_max', sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column('education_requirement', sa.String(length=255), nullable=True),
        sa.Column('salary_min', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('salary_max', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            'status',
            sa.String(length=20),
            server_default='draft',
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
        sa.ForeignKeyConstraint(
            ['company_id'],
            ['companies.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )

    # Individual-column indexes
    op.create_index(op.f('ix_jobs_company_id'), 'jobs', ['company_id'], unique=False)
    op.create_index(op.f('ix_jobs_status'), 'jobs', ['status'], unique=False)
    op.create_index(op.f('ix_jobs_title'), 'jobs', ['title'], unique=False)

    # Composite index: recruiter listing filtered by company + status
    op.create_index('ix_jobs_company_status', 'jobs', ['company_id', 'status'], unique=False)


def downgrade() -> None:
    """Downgrade schema — drop jobs table."""
    op.drop_index('ix_jobs_company_status', table_name='jobs')
    op.drop_index(op.f('ix_jobs_title'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_status'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_company_id'), table_name='jobs')
    op.drop_table('jobs')
