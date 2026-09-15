"""harden applicant_skills: add timestamps, server_default, unique constraint

Revision ID: b7e8f9a0b1c2
Revises: a1b2c3d4e5f6
Create Date: 2026-09-15 01:50:00.000000

Changes:
- Add created_at (TIMESTAMPTZ, server_default NOW())
- Add updated_at (TIMESTAMPTZ, server_default NOW())
- Add server_default 'beginner' to proficiency_level column
- Add UNIQUE constraint on (user_id, skill_name)

Safety: The upgrade() function first checks for duplicate (user_id, skill_name)
rows before attempting to add the unique constraint. If duplicates exist the
migration STOPS with a descriptive error rather than silently deleting data.
Existing rows receive NOW() for both timestamp columns via the server_default.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = 'b7e8f9a0b1c2'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    # ------------------------------------------------------------------
    # Safety check: abort if duplicate (user_id, skill_name) rows exist.
    # We do a case-sensitive check here because that is what a UNIQUE
    # constraint enforces at the DB level.  The API layer already prevents
    # case-insensitive duplicates, so case-sensitive duplicates should be
    # impossible in practice—but we verify to be safe.
    # ------------------------------------------------------------------
    result = bind.execute(
        sa.text(
            """
            SELECT user_id, skill_name, COUNT(*) AS cnt
            FROM applicant_skills
            GROUP BY user_id, skill_name
            HAVING COUNT(*) > 1
            """
        )
    )
    duplicates = result.fetchall()
    if duplicates:
        lines = "\n".join(
            f"  user_id={row[0]}, skill_name='{row[1]}', count={row[2]}"
            for row in duplicates
        )
        raise RuntimeError(
            "Migration aborted: duplicate (user_id, skill_name) rows found in "
            "applicant_skills. Resolve duplicates manually before re-running.\n"
            f"{lines}"
        )

    # ------------------------------------------------------------------
    # 1. Add created_at column with server_default NOW()
    #    Existing rows will receive the current timestamp automatically.
    # ------------------------------------------------------------------
    op.add_column(
        "applicant_skills",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # ------------------------------------------------------------------
    # 2. Add updated_at column with server_default NOW()
    # ------------------------------------------------------------------
    op.add_column(
        "applicant_skills",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # ------------------------------------------------------------------
    # 3. Add server_default 'beginner' to existing proficiency_level column.
    #    The column already exists and is NOT NULL; we only set the
    #    server_default so that DB-level inserts (e.g. psql shell) also
    #    get the default.
    # ------------------------------------------------------------------
    op.alter_column(
        "applicant_skills",
        "proficiency_level",
        existing_type=sa.String(length=50),
        server_default="beginner",
        existing_nullable=False,
    )

    # ------------------------------------------------------------------
    # 4. Add UNIQUE constraint on (user_id, skill_name).
    #    Safe because duplicates were verified absent above.
    # ------------------------------------------------------------------
    op.create_unique_constraint(
        "uq_applicant_skills_user_skill",
        "applicant_skills",
        ["user_id", "skill_name"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_applicant_skills_user_skill",
        "applicant_skills",
        type_="unique",
    )
    op.alter_column(
        "applicant_skills",
        "proficiency_level",
        existing_type=sa.String(length=50),
        server_default=None,
        existing_nullable=False,
    )
    op.drop_column("applicant_skills", "updated_at")
    op.drop_column("applicant_skills", "created_at")
