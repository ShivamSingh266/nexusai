"""Load persisted applicant data into the shared canonical SkillProfile."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.representations import SkillProfile, SkillProfileSkill
from app.models.applicant_profile import ApplicantProfile
from app.models.applicant_skill import ApplicantSkill
from app.models.canonical_skill import CanonicalSkill
from app.models.user import User


class SkillProfileLoadError(Exception):
    """Base error for invalid or unavailable persisted candidate data."""


class CandidateNotFoundError(SkillProfileLoadError):
    """The requested candidate user does not exist."""


class CandidateProfileNotFoundError(SkillProfileLoadError):
    """The candidate exists but has no applicant profile."""


class CandidateSkillValidationError(SkillProfileLoadError):
    """Persisted candidate skill data is not canonical or version-consistent."""


def load_candidate_skill_profile(
    db: Session,
    candidate_id: int,
    *,
    taxonomy_version: str | None = None,
) -> SkillProfile:
    """Load one applicant's persisted profile and canonical skills.

    Legacy free-text ApplicantSkill rows have no ``skill_id`` and are omitted.
    Canonical rows must reference an existing taxonomy record whose version
    matches the requested profile version. Proficiency and experience are
    copied exactly as stored; this loader never infers either value.
    """
    candidate = db.scalar(select(User).where(User.id == candidate_id))
    if candidate is None:
        raise CandidateNotFoundError(f"Candidate not found: {candidate_id}")

    profile = db.scalar(
        select(ApplicantProfile).where(ApplicantProfile.user_id == candidate_id)
    )
    if profile is None:
        raise CandidateProfileNotFoundError(
            f"Applicant profile not found: {candidate_id}"
        )

    expected_version = taxonomy_version or settings.TAXONOMY_VERSION

    persisted_skills = db.scalars(
        select(ApplicantSkill)
        .where(ApplicantSkill.user_id == candidate_id)
        .order_by(ApplicantSkill.id)
    ).all()

    skills: list[SkillProfileSkill] = []

    for persisted_skill in persisted_skills:
        if persisted_skill.skill_id is None:
            continue

        canonical_skill = db.get(CanonicalSkill, persisted_skill.skill_id)

        if canonical_skill is None:
            raise CandidateSkillValidationError(
                f"Canonical skill not found: {persisted_skill.skill_id}"
            )

        if persisted_skill.taxonomy_version != expected_version:
            raise CandidateSkillValidationError(
                f"Applicant skill taxonomy mismatch: {persisted_skill.skill_id}"
            )

        if canonical_skill.taxonomy_version != persisted_skill.taxonomy_version:
            raise CandidateSkillValidationError(
                f"Canonical taxonomy mismatch: {persisted_skill.skill_id}"
            )

        skills.append(
            SkillProfileSkill(
                skill_id=persisted_skill.skill_id,
                taxonomy_version=persisted_skill.taxonomy_version,
                proficiency_level=persisted_skill.proficiency_level,
                years_experience=persisted_skill.years_experience,
            )
        )

    semantic_parts = [
        part.strip()
        for part in (
            profile.bio,
            profile.education,
        )
        if part and part.strip()
    ]

    return SkillProfile(
        subject_id=candidate_id,
        subject_type="applicant",
        taxonomy_version=expected_version,
        skills=tuple(skills),
        location=profile.location,
        education=profile.education,
        experience_years=profile.experience_years,
        semantic_text=" ".join(semantic_parts) or None,
    )