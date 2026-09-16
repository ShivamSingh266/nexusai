import pytest

from app.core.representations import (
    SkillProfile,
    SkillProfileSkill,
)


def test_skill_profile_skill_stores_canonical_identity() -> None:
    skill = SkillProfileSkill(
        skill_id="SKILL_0001",
        taxonomy_version="v1.2.1",
        proficiency_level="advanced",
        years_experience=3,
    )

    assert skill.skill_id == "SKILL_0001"
    assert skill.taxonomy_version == "v1.2.1"
    assert skill.proficiency_level == "advanced"
    assert skill.years_experience == 3


def test_skill_profile_stores_candidate_metadata() -> None:
    profile = SkillProfile(
        subject_id=101,
        subject_type="applicant",
        taxonomy_version="v1.2.1",
        skills=(
            SkillProfileSkill(
                skill_id="SKILL_0001",
                taxonomy_version="v1.2.1",
            ),
        ),
        location="Pune",
        education="B.Tech",
        experience_years=4.0,
    )

    assert profile.subject_id == 101
    assert profile.subject_type == "applicant"
    assert profile.taxonomy_version == "v1.2.1"
    assert profile.location == "Pune"
    assert profile.education == "B.Tech"
    assert profile.experience_years == pytest.approx(4.0)


def test_profile_can_contain_multiple_canonical_skills() -> None:
    profile = SkillProfile(
        subject_id=101,
        subject_type="applicant",
        taxonomy_version="v1.2.1",
        skills=(
            SkillProfileSkill(
                skill_id="SKILL_0001",
                taxonomy_version="v1.2.1",
            ),
            SkillProfileSkill(
                skill_id="SKILL_0002",
                taxonomy_version="v1.2.1",
            ),
        ),
    )

    assert [skill.skill_id for skill in profile.skills] == [
        "SKILL_0001",
        "SKILL_0002",
    ]


def test_skill_profile_has_no_inferred_proficiency() -> None:
    skill = SkillProfileSkill(
        skill_id="SKILL_0001",
        taxonomy_version="v1.2.1",
    )

    assert skill.proficiency_level is None
    assert skill.years_experience is None