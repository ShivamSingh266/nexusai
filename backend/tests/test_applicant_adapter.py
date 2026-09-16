import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.applicant_adapter import build_applicant_skill_profile
from app.db.base import Base
from app.models.applicant_profile import ApplicantProfile
from app.models.applicant_skill import ApplicantSkill
from app.models.canonical_skill import CanonicalSkill, SkillAlias


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(
        engine,
        tables=[
            CanonicalSkill.__table__,
            SkillAlias.__table__,
            ApplicantProfile.__table__,
            ApplicantSkill.__table__,
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
                taxonomy_version="v1.2.1",
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


def test_applicant_skill_is_converted_to_canonical_id(
    db: Session,
) -> None:
    profile = ApplicantProfile(
        user_id=101,
        experience_years=3.0,
        location="Pune",
        education="B.Tech",
        bio="Python developer",
    )

    skill = ApplicantSkill(
        user_id=101,
        skill_name="Python",
        proficiency_level="advanced",
        years_experience=3,
    )

    db.add_all([profile, skill])
    db.commit()
    db.refresh(skill)

    result, unresolved = build_applicant_skill_profile(
        profile,
        [skill],
        db,
    )

    assert result.subject_id == 101
    assert result.subject_type == "applicant"
    assert result.taxonomy_version == "v1.2.1"
    assert [item.skill_id for item in result.skills] == ["SKILL_0001"]
    assert result.skills[0].proficiency_level == "advanced"
    assert result.skills[0].years_experience == 3
    assert unresolved == []


def test_alias_is_resolved_to_canonical_id(
    db: Session,
) -> None:
    profile = ApplicantProfile(
        user_id=102,
        experience_years=2.0,
    )

    skill = ApplicantSkill(
        user_id=102,
        skill_name="Python programming",
        proficiency_level="expert",
    )

    db.add_all([profile, skill])
    db.commit()
    db.refresh(skill)

    result, unresolved = build_applicant_skill_profile(
        profile,
        [skill],
        db,
    )

    assert [item.skill_id for item in result.skills] == ["SKILL_0001"]
    assert result.skills[0].proficiency_level == "expert"
    assert unresolved == []


def test_unknown_skill_is_reported_not_invented(
    db: Session,
) -> None:
    profile = ApplicantProfile(
        user_id=103,
        experience_years=1.0,
    )

    skill = ApplicantSkill(
        user_id=103,
        skill_name="Unknown Technology",
        proficiency_level="beginner",
    )

    db.add_all([profile, skill])
    db.commit()
    db.refresh(skill)

    result, unresolved = build_applicant_skill_profile(
        profile,
        [skill],
        db,
    )

    assert result.skills == ()
    assert unresolved == ["Unknown Technology"]


def test_multiple_skills_are_deterministic(
    db: Session,
) -> None:
    profile = ApplicantProfile(
        user_id=104,
        experience_years=4.0,
    )

    skills = [
        ApplicantSkill(
            user_id=104,
            skill_name="Python",
            proficiency_level="beginner",
        ),
        ApplicantSkill(
            user_id=104,
            skill_name="Python programming",
            proficiency_level="expert",
        ),
    ]

    db.add_all([profile, *skills])
    db.commit()

    for skill in skills:
        db.refresh(skill)

    result, unresolved = build_applicant_skill_profile(
        profile,
        skills,
        db,
    )

    assert [item.skill_id for item in result.skills] == [
        "SKILL_0001",
        "SKILL_0001",
    ]
    assert [item.proficiency_level for item in result.skills] == [
        "beginner",
        "expert",
    ]
    assert unresolved == []