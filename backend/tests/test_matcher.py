import pytest

from app.core.matcher import SCORING_VERSION, match_profiles
from app.core.representations import SkillEntry, SkillProfile


def make_candidate() -> SkillProfile:
    profile = SkillProfile(
        owner_id="candidate-1",
        kind="candidate",
        experience_years=4,
        education_level=0.8,
        location="Pune",
        work_mode="remote",
        text="Python SQL data engineering",
    )

    profile.add_skill(
        SkillEntry(
            skill_id="SKILL_0001",
            proficiency=0.9,
            proficiency_level="expert",
        )
    )

    profile.add_skill(
        SkillEntry(
            skill_id="SKILL_0002",
            proficiency=0.7,
            proficiency_level="advanced",
        )
    )

    return profile


def make_job() -> SkillProfile:
    profile = SkillProfile(
        owner_id="job-1",
        kind="job",
        experience_years=3,
        education_level=0.8,
        location="Pune",
        work_mode="remote",
        text="Python SQL data engineering",
    )

    profile.add_skill(
        SkillEntry(
            skill_id="SKILL_0001",
            proficiency=0.5,
            proficiency_level="intermediate",
            min_proficiency=0.5,
        )
    )

    profile.add_skill(
        SkillEntry(
            skill_id="SKILL_0002",
            proficiency=0.5,
            proficiency_level="intermediate",
            min_proficiency=0.5,
        )
    )

    profile.add_skill(
        SkillEntry(
            skill_id="SKILL_0003",
            proficiency=0.5,
            proficiency_level="intermediate",
            min_proficiency=0.5,
        )
    )

    return profile


def test_match_returns_matched_and_missing_skills() -> None:
    result = match_profiles(make_candidate(), make_job())

    assert result.matched_skills == ["SKILL_0001", "SKILL_0002"]
    assert result.missing_skills == ["SKILL_0003"]


def test_all_score_components_are_returned() -> None:
    result = match_profiles(make_candidate(), make_job())

    assert result.skill_score == pytest.approx(2 / 3)
    assert result.semantic_score == pytest.approx(1.0)
    assert result.experience_score == pytest.approx(1.0)
    assert result.education_score == pytest.approx(1.0)
    assert result.location_mode_score == pytest.approx(1.0)


def test_final_score_uses_weighted_contract() -> None:
    result = match_profiles(make_candidate(), make_job())

    expected = (
        (2 / 3) * 0.60
        + 1.0 * 0.20
        + 1.0 * 0.10
        + 1.0 * 0.05
        + 1.0 * 0.05
    )

    assert result.final_score == pytest.approx(expected)


def test_missing_optional_components_are_renormalized() -> None:
    candidate = make_candidate()
    target = make_job()

    candidate.experience_years = None
    candidate.education_level = None
    candidate.location = None
    candidate.work_mode = None

    target.experience_years = None
    target.education_level = None
    target.location = None
    target.work_mode = None

    result = match_profiles(candidate, target)

    expected = (
        (2 / 3) * 0.60
        + 1.0 * 0.20
    ) / (0.60 + 0.20)

    assert result.final_score == pytest.approx(expected)


def test_scoring_version_and_explanation_are_present() -> None:
    result = match_profiles(make_candidate(), make_job())

    assert result.scoring_version == SCORING_VERSION
    assert result.explanation
    assert "final=" in result.explanation
    assert "version=" in result.explanation


def test_same_matcher_supports_reverse_direction() -> None:
    candidate = make_candidate()
    job = make_job()

    forward = match_profiles(candidate, job)
    reverse = match_profiles(job, candidate)

    assert forward.final_score != reverse.final_score
    assert reverse.scoring_version == SCORING_VERSION