from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.representations import (
    SkillEntry,
    SkillProfile,
    normalize_proficiency,
)
from app.core.taxonomy_resolver import resolve_canonical_skill_id
from app.models.applicant_profile import ApplicantProfile
from app.models.applicant_skill import ApplicantSkill


def build_applicant_skill_profile(
    applicant_profile: ApplicantProfile,
    applicant_skills: list[ApplicantSkill],
    db: Session,
) -> tuple[SkillProfile, list[str]]:
    """
    Convert existing applicant database records into the Member 5
    canonical SkillProfile representation.

    Returns:
        (profile, unresolved_skill_names)

    Unresolved skill names are reported rather than silently invented.
    """
    profile = SkillProfile(
        owner_id=str(applicant_profile.user_id),
        kind="candidate",
        experience_years=applicant_profile.experience_years,
        location=applicant_profile.location,
        text=applicant_profile.bio or "",
    )

    unresolved: list[str] = []

    for applicant_skill in applicant_skills:
        canonical_id = resolve_canonical_skill_id(
            applicant_skill.skill_name,
            db,
        )

        if canonical_id is None:
            unresolved.append(applicant_skill.skill_name)
            continue

        proficiency_level = normalize_proficiency(
            applicant_skill.proficiency_level
        )

        entry = SkillEntry(
            skill_id=canonical_id,
            proficiency=proficiency_level,
            proficiency_level=applicant_skill.proficiency_level,
            evidence=(
                f"ApplicantSkill:{applicant_skill.id}",
            ),
        )

        profile.add_skill(entry)

    return profile, sorted(set(unresolved))