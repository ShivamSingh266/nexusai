"""fix canonical skill id constraint

Revision ID: c6486a04695f
Revises: d4e5f6a7b8c9
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c6486a04695f"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_canonical_skills_skill_id_format",
        "canonical_skills",
        type_="check",
    )

    op.create_check_constraint(
        "ck_canonical_skills_skill_id_format",
        "canonical_skills",
        "skill_id ~ '^SKILL_[0-9]{4}$'",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_canonical_skills_skill_id_format",
        "canonical_skills",
        type_="check",
    )

    op.create_check_constraint(
        "ck_canonical_skills_skill_id_format",
        "canonical_skills",
        "skill_id LIKE 'SKILL____' AND length(skill_id) = 10",
    )