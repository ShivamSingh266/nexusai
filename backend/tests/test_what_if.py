from __future__ import annotations

import pytest

from app.core.what_if import career_what_if
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
        experience_years=3.0,
        education="Computer Science",
        location="Pune",
    )


def make_job() -> Job:
    job = Job(
        id=1,
        company_id=1,
        title="What-If Test Job",
        status="published",
        experience_min=2.0,
        experience_max=5.0,
        education_requirement="Computer Science",
        location="Pune",
        work_mode="remote",
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


def test_what_if_reduces_skill_gaps() -> None:
    result = career_what_if(
        make_candidate(),
        make_job(),
        {
            "SKILL_0002": SkillProfileSkill(
                skill_id="SKILL_0002",
                taxonomy_version="v1.2.1",
                proficiency_level="expert",
            )
        },
    )

    assert len(result.baseline_gaps) == 1
    assert len(result.hypothetical_gaps) == 0
    assert result.gap_count_change == -1


def test_what_if_improves_match_score() -> None:
    result = career_what_if(
        make_candidate(),
        make_job(),
        {
            "SKILL_0002": SkillProfileSkill(
                skill_id="SKILL_0002",
                taxonomy_version="v1.2.1",
                proficiency_level="expert",
            )
        },
    )

    assert (
        result.hypothetical_match.final_score
        > result.baseline_match.final_score
    )
    assert result.match_score_change > 0.0


def test_what_if_does_not_mutate_candidate() -> None:
    candidate = make_candidate()

    career_what_if(
        candidate,
        make_job(),
        {
            "SKILL_0002": SkillProfileSkill(
                skill_id="SKILL_0002",
                taxonomy_version="v1.2.1",
                proficiency_level="expert",
            )
        },
    )

    assert [skill.skill_id for skill in candidate.skills] == [
        "SKILL_0001"
    ]


def test_what_if_keeps_scoring_version() -> None:
    result = career_what_if(
        make_candidate(),
        make_job(),
        {},
    )

    assert result.baseline_match.scoring_version
    assert result.hypothetical_match.scoring_version


def test_what_if_with_no_new_skill_keeps_score() -> None:
    result = career_what_if(
        make_candidate(),
        make_job(),
        {},
    )

    assert result.match_score_change == pytest.approx(0.0)
    assert result.gap_count_change == 0
    assert (
        result.baseline_match.final_score
        == pytest.approx(result.hypothetical_match.final_score)
    )