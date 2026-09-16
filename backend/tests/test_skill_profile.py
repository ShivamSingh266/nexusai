"""Tests for loading persisted applicants into the canonical SkillProfile."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.applicant_profile import ApplicantProfile
from app.models.applicant_skill import ApplicantSkill
from app.models.canonical_skill import CanonicalSkill
from app.models.user import Role, User
from app.services.skill_profile import (
    CandidateNotFoundError,
    CandidateProfileNotFoundError,
    CandidateSkillValidationError,
    load_candidate_skill_profile,
)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session: Session = session_factory()
    role = Role(name="applicant", description="Applicant")
    session.add(role)
    session.flush()
    session.add_all(
        [
            CanonicalSkill(
                skill_id="SKILL_0001",
                canonical_name="Python",
                normalized_name="python",
                category="technical",
                source="ESCO",
                taxonomy_version="v1.2.1",
            ),
            CanonicalSkill(
                skill_id="SKILL_0002",
                canonical_name="SQL",
                normalized_name="sql",
                category="technical",
                source="ESCO",
                taxonomy_version="v1.2.1",
            ),
        ]
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def add_candidate(
    db: Session,
    *,
    email: str = "candidate@example.com",
    with_profile: bool = True,
) -> User:
    role = db.query(Role).filter(Role.name == "applicant").one()
    candidate = User(
        email=email,
        password_hash="test-hash",
        full_name="Candidate",
        role_id=role.id,
    )
    db.add(candidate)
    db.flush()
    if with_profile:
        db.add(
            ApplicantProfile(
                user_id=candidate.id,
                location="Pune",
                education="BSc Computer Science",
                experience_years=3,
            )
        )
    db.commit()
    return candidate


def test_loads_persisted_canonical_profile_and_skills(db: Session):
    candidate = add_candidate(db)
    db.add_all(
        [
            ApplicantSkill(
                user_id=candidate.id,
                skill_name="Python",
                skill_id="SKILL_0001",
                taxonomy_version="v1.2.1",
                proficiency_level="intermediate",
                years_experience=2,
            ),
            ApplicantSkill(
                user_id=candidate.id,
                skill_name="SQL",
                skill_id="SKILL_0002",
                taxonomy_version="v1.2.1",
                proficiency_level="beginner",
                years_experience=None,
            ),
        ]
    )
    db.commit()

    profile = load_candidate_skill_profile(db, candidate.id)

    assert profile.subject_id == candidate.id
    assert profile.subject_type == "applicant"
    assert profile.taxonomy_version == "v1.2.1"
    assert profile.location == "Pune"
    assert profile.education == "BSc Computer Science"
    assert profile.experience_years == 3
    assert [skill.skill_id for skill in profile.skills] == ["SKILL_0001", "SKILL_0002"]
    assert profile.skills[0].proficiency_level == "intermediate"
    assert profile.skills[0].years_experience == 2


def test_legacy_free_text_is_excluded_and_nullable_experience_is_preserved(db: Session):
    candidate = add_candidate(db, email="legacy@example.com")
    db.add_all(
        [
            ApplicantSkill(
                user_id=candidate.id,
                skill_name="Legacy free text",
                proficiency_level="beginner",
                years_experience=None,
            ),
            ApplicantSkill(
                user_id=candidate.id,
                skill_name="Python",
                skill_id="SKILL_0001",
                taxonomy_version="v1.2.1",
                proficiency_level="intermediate",
                years_experience=None,
            ),
        ]
    )
    db.commit()

    profile = load_candidate_skill_profile(db, candidate.id)

    assert [skill.skill_id for skill in profile.skills] == ["SKILL_0001"]
    assert profile.skills[0].years_experience is None
    assert profile.skills[0].proficiency_level == "intermediate"


def test_missing_candidate_and_profile_are_distinguished(db: Session):
    with pytest.raises(CandidateNotFoundError):
        load_candidate_skill_profile(db, 999999)

    candidate = add_candidate(db, email="no-profile@example.com", with_profile=False)
    with pytest.raises(CandidateProfileNotFoundError):
        load_candidate_skill_profile(db, candidate.id)


def test_taxonomy_version_mismatch_is_rejected(db: Session):
    candidate = add_candidate(db, email="version@example.com")
    db.add(
        ApplicantSkill(
            user_id=candidate.id,
            skill_name="Python",
            skill_id="SKILL_0001",
            taxonomy_version="v9.9.9",
            proficiency_level="intermediate",
        )
    )
    db.commit()

    with pytest.raises(CandidateSkillValidationError):
        load_candidate_skill_profile(db, candidate.id)


def test_missing_canonical_skill_is_rejected(db: Session):
    candidate = add_candidate(db, email="invalid-skill@example.com")
    db.add(
        ApplicantSkill(
            user_id=candidate.id,
            skill_name="Invalid",
            skill_id="SKILL_9999",
            taxonomy_version="v1.2.1",
            proficiency_level="beginner",
        )
    )
    db.commit()

    with pytest.raises(CandidateSkillValidationError):
        load_candidate_skill_profile(db, candidate.id)
