from __future__ import annotations

import re
import unicodedata

from sqlalchemy.orm import Session

from app.models.canonical_skill import CanonicalSkill, SkillAlias


def normalize_skill_text(text: str) -> str:
    """
    Normalize skill text using the same normalization contract as taxonomy.py.
    """
    text = unicodedata.normalize("NFKD", text)
    text = text.strip().lower()
    return re.sub(r"\s+", " ", text)


def resolve_canonical_skill_id(
    skill_name: str,
    db: Session,
) -> str | None:
    """
    Resolve a stored skill name to an existing canonical SKILL_XXXX ID.

    Resolution order:
    1. Exact canonical normalized_name.
    2. Exact normalized_alias.

    No new skill IDs are created.
    No substring/approximate mapping is performed here.
    """
    normalized = normalize_skill_text(skill_name)

    if not normalized:
        return None

    canonical = (
        db.query(CanonicalSkill)
        .filter(
            CanonicalSkill.normalized_name == normalized,
            CanonicalSkill.is_active.is_(True),
        )
        .order_by(CanonicalSkill.skill_id)
        .first()
    )

    if canonical is not None:
        return canonical.skill_id

    alias = (
        db.query(SkillAlias)
        .join(
            CanonicalSkill,
            SkillAlias.skill_id == CanonicalSkill.skill_id,
        )
        .filter(
            SkillAlias.normalized_alias == normalized,
            CanonicalSkill.is_active.is_(True),
        )
        .order_by(
            SkillAlias.skill_id,
            SkillAlias.id,
        )
        .first()
    )

    if alias is not None:
        return alias.skill_id

    return None