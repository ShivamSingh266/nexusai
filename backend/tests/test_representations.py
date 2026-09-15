import pytest

from app.core.representations import (
    SkillEntry,
    SkillProfile,
    normalize_proficiency,
)


def test_proficiency_normalization() -> None:
    assert normalize_proficiency("beginner") == 0.25
    assert normalize_proficiency("intermediate") == 0.50
    assert normalize_proficiency("advanced") == 0.75
    assert normalize_proficiency("expert") == 1.00


def test_proficiency_is_case_and_whitespace_tolerant() -> None:
    assert normalize_proficiency(" Expert ") == 1.00


def test_unknown_proficiency_raises() -> None:
    with pytest.raises(ValueError):
        normalize_proficiency("master")


def test_candidate_profile() -> None:
    profile = SkillProfile(
        owner_id=1,
        kind="candidate",
        experience_years=3.0,
        education_level=0.75,
        location="Pune",
        work_mode="hybrid",
    )

    profile.add_skill(
        SkillEntry(
            skill_id="SKILL_0400",
            proficiency=0.75,
            proficiency_level="advanced",
            evidence="project",
        )
    )

    assert profile.has_skill("SKILL_0400")
    assert profile.skills["SKILL_0400"].proficiency == 0.75
    assert profile.location == "Pune"


def test_target_profile() -> None:
    profile = SkillProfile(
        owner_id=100,
        kind="job",
        experience_years=2.0,
        location="Pune",
        work_mode="hybrid",
    )

    profile.add_skill(
        SkillEntry(
            skill_id="SKILL_0400",
            importance=1.0,
            min_proficiency=0.60,
        )
    )

    assert profile.has_skill("SKILL_0400")
    assert profile.skills["SKILL_0400"].importance == 1.0
    assert profile.skills["SKILL_0400"].min_proficiency == 0.60