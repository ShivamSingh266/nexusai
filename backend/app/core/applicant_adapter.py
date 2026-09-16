from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.representations import SkillProfile, SkillProfileSkill
from app.core.taxonomy_resolver import resolve_canonical_skill_id
from app.models.applicant_profile import ApplicantProfile
from app.models.applicant_skill import ApplicantSkill


DEFAULT_TAXONOMY_VERSION = "v1.2.1"


def build_applicant_skill_profile(
    applicant_profile: ApplicantProfile,
    applicant_skills: list[ApplicantSkill],
    db: Session,
) -> tuple[SkillProfile, list[str]]:
    """
    Convert persisted applicant records into the shared SkillProfile.

    Existing canonical ApplicantSkill.skill_id is preferred.
    Name resolution is used only when skill_id is absent.
    """
    unresolved: list[str] = []
    skills: list[SkillProfileSkill] = []

    taxonomy_versions = {
        skill.taxonomy_version
        for skill in applicant_skills
        if skill.skill_id and skill.taxonomy_version
    }

    taxonomy_version = (
        sorted(taxonomy_versions)[0]
        if taxonomy_versions
        else DEFAULT_TAXONOMY_VERSION
    )

    for applicant_skill in applicant_skills:
        skill_id = applicant_skill.skill_id

        if skill_id is None:
            skill_id = resolve_canonical_skill_id(
                applicant_skill.skill_name,
                db,
            )

        if skill_id is None:
            unresolved.append(applicant_skill.skill_name)
            continue

        skills.append(
            SkillProfileSkill(
                skill_id=skill_id,
                taxonomy_version=(
                    applicant_skill.taxonomy_version
                    or taxonomy_version
                ),
                proficiency_level=applicant_skill.proficiency_level,
                years_experience=applicant_skill.years_experience,
            )
        )

    return (
        SkillProfile(
            subject_id=applicant_profile.user_id,
            subject_type="applicant",
            taxonomy_version=taxonomy_version,
            skills=tuple(skills),
            location=applicant_profile.location,
            education=applicant_profile.education,
            experience_years=applicant_profile.experience_years,
        ),
        sorted(set(unresolved)),
    )