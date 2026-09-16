import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.taxonomy_resolver import (
    normalize_skill_text,
    resolve_canonical_skill_id,
)
from app.db.base import Base
from app.models.canonical_skill import CanonicalSkill, SkillAlias


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(
        engine,
        tables=[
            CanonicalSkill.__table__,
            SkillAlias.__table__,
        ],
    )

    with Session(engine) as session:
        session.add(
            CanonicalSkill(
                skill_id="SKILL_0001",
                canonical_name="Python",
                normalized_name="python",
                category="Programming",
                source="ESCO",
                taxonomy_version="test-v1",
                is_active=True,
            )
        )

        session.add(
            CanonicalSkill(
                skill_id="SKILL_0002",
                canonical_name="C++",
                normalized_name="c++",
                category="Programming",
                source="ESCO",
                taxonomy_version="test-v1",
                is_active=True,
            )
        )

        session.add(
            SkillAlias(
                alias="Python programming",
                normalized_alias="python programming",
                skill_id="SKILL_0001",
                confidence=0.95,
            )
        )

        session.commit()

        yield session


def test_normalization_matches_taxonomy_contract() -> None:
    assert normalize_skill_text("  PYTHON   PROGRAMMING  ") == (
        "python programming"
    )


def test_exact_canonical_name_resolves(db: Session) -> None:
    assert resolve_canonical_skill_id("Python", db) == "SKILL_0001"


def test_exact_alias_resolves(db: Session) -> None:
    assert resolve_canonical_skill_id(
        "Python programming",
        db,
    ) == "SKILL_0001"


def test_resolution_is_case_and_whitespace_insensitive(db: Session) -> None:
    assert resolve_canonical_skill_id(
        "  PYTHON  ",
        db,
    ) == "SKILL_0001"


def test_unknown_skill_returns_none(db: Session) -> None:
    assert resolve_canonical_skill_id(
        "Something Unknown",
        db,
    ) is None


def test_inactive_skill_is_not_resolved(db: Session) -> None:
    db.add(
        CanonicalSkill(
            skill_id="SKILL_0003",
            canonical_name="Inactive Skill",
            normalized_name="inactive skill",
            category="Test",
            source="ESCO",
            taxonomy_version="test-v1",
            is_active=False,
        )
    )
    db.commit()

    assert resolve_canonical_skill_id(
        "Inactive Skill",
        db,
    ) is None


def test_substring_is_not_used_for_resolution(db: Session) -> None:
    assert resolve_canonical_skill_id(
        "python developer",
        db,
    ) is None