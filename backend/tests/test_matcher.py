from __future__ import annotations

import pytest

from app.core.matching import MATCHING_VERSION, match_candidate_to_job
from app.core.representations import SkillProfile, SkillProfileSkill
from app.models.job import Job
from app.models.job_skill import JobSkill


def make_candidate(
    skill_ids: tuple[str, ...] = ("SKILL_0001",),
) -> SkillProfile:
    return SkillProfile(
        subject_id=1,
        subject_type="applicant",
        taxonomy_version="v1.2.1",
        skills=tuple(
            SkillProfileSkill(
                skill_id=skill_id,
                taxonomy_version="v1.2.1",
                proficiency_level="expert",
            )
            for skill_id in skill_ids
        ),
        experience_years=4.0,
        education="B.Tech Computer Science",
        location="Pune",
    )


def make_job() -> Job:
    job = Job(
        id=1,
        company_id=1,
        title="Matching Engineer",
        status="published",
        experience_min=3.0,
        experience_max=5.0,
        education_requirement="Computer Science",
        location="Pune",
        work_mode="onsite",
    )

    job.job_skills = [
        JobSkill(
            id=1,
            job_id=1,
            skill_id="SKILL_0001",
            taxonomy_version="v1.2.1",
            role_importance=1.0,
        ),
        JobSkill(
            id=2,
            job_id=1,
            skill_id="SKILL_0002",
            taxonomy_version="v1.2.1",
            role_importance=1.0,
        ),
    ]

    return job


def test_match_returns_required_components() -> None:
    result = match_candidate_to_job(
        make_candidate(),
        make_job(),
    )

    assert result.component_scores["skill_coverage"] == pytest.approx(0.5)
    assert result.component_scores["experience"] == pytest.approx(1.0)
    assert result.component_scores["education"] == pytest.approx(1.0)
    assert result.component_scores["location_work_mode"] == pytest.approx(1.0)


def test_match_renormalizes_missing_optional_components() -> None:
    candidate = SkillProfile(
        subject_id=1,
        subject_type="applicant",
        taxonomy_version="v1.2.1",
        skills=(
            SkillProfileSkill(
                skill_id="SKILL_0001",
                taxonomy_version="v1.2.1",
            ),
        ),
    )

    job = Job(
        id=1,
        company_id=1,
        title="Skills Only",
        status="published",
    )

    job.job_skills = [
        JobSkill(
            id=1,
            job_id=1,
            skill_id="SKILL_0001",
            taxonomy_version="v1.2.1",
            role_importance=1.0,
        ),
    ]

    result = match_candidate_to_job(candidate, job)

    assert result.available_components == ("skill_coverage",)
    assert set(result.omitted_components) == {
        "semantic_similarity",
        "experience",
        "education",
        "location_work_mode",
    }
    assert result.score == pytest.approx(1.0)


def test_matching_version_is_returned() -> None:
    result = match_candidate_to_job(
        make_candidate(),
        make_job(),
    )

    assert MATCHING_VERSION == "matching-v1"
    assert result.explanation
    assert result.warnings is not None


def test_taxonomy_mismatch_raises() -> None:
    candidate = make_candidate()

    job = make_job()
    job.job_skills = [
        JobSkill(
            id=1,
            job_id=1,
            skill_id="SKILL_0001",
            taxonomy_version="wrong-version",
            role_importance=1.0,
        ),
    ]

    with pytest.raises(Exception, match="Taxonomy version mismatch"):
        match_candidate_to_job(candidate, job)


def test_missing_job_skills_raises() -> None:
    from app.core.matching import NoUsableJobSkillsError

    candidate = make_candidate()

    job = Job(
        id=1,
        company_id=1,
        title="Empty",
        status="published",
    )

    with pytest.raises(NoUsableJobSkillsError):
        match_candidate_to_job(candidate, job)