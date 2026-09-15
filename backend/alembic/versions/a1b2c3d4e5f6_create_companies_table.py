"""create companies table and add company_id to users

Revision ID: a1b2c3d4e5f6
Revises: 5259f92e15f1
Create Date: 2026-09-15 01:34:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '5259f92e15f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the companies table first (no FK dependencies)
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('industry', sa.String(length=150), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('company_size', sa.String(length=50), nullable=True),
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
        sa.PrimaryKeyConstraint('id'),
    )

    # Add nullable company_id FK column to users
    op.add_column(
        'users',
        sa.Column('company_id', sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f('ix_users_company_id'),
        'users',
        ['company_id'],
        unique=False,
    )
    op.create_foreign_key(
        'fk_users_company_id_companies',
        'users',
        'companies',
        ['company_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'fk_users_company_id_companies',
        'users',
        type_='foreignkey',
    )
    op.drop_index(op.f('ix_users_company_id'), table_name='users')
    op.drop_column('users', 'company_id')
    op.drop_table('companies')
