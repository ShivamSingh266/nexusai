from __future__ import annotations

from app.core.ranking import rank_candidates
from app.core.representations import SkillProfile, SkillProfileSkill
from app.models.job import Job
from app.models.job_skill import JobSkill


def make_job() -> Job:
    job = Job(
        id=1,
        company_id=1,
        title="Ranking Test",
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
        JobSkill(
            id=2,
            job_id=1,
            skill_id="SKILL_0002",
            taxonomy_version="v1.2.1",
            role_importance=1.0,
        ),
    ]

    return job


def make_candidate(
    candidate_id: int,
    skill_ids: tuple[str, ...],
) -> tuple[int, SkillProfile]:
    return (
        candidate_id,
        SkillProfile(
            subject_id=candidate_id,
            subject_type="applicant",
            taxonomy_version="v1.2.1",
            skills=tuple(
                SkillProfileSkill(
                    skill_id=skill_id,
                    taxonomy_version="v1.2.1",
                )
                for skill_id in skill_ids
            ),
        ),
    )


def test_rank_candidates_orders_by_match_score() -> None:
    job = make_job()

    candidates = [
        make_candidate(2, ("SKILL_0001",)),
        make_candidate(1, ("SKILL_0001", "SKILL_0002")),
    ]

    ranked = rank_candidates(
        job,
        candidates,
    )

    assert [item.candidate_id for item in ranked] == [1, 2]


def test_ranking_is_deterministic_for_equal_candidates() -> None:
    job = make_job()

    candidates = [
        make_candidate(2, ("SKILL_0001",)),
        make_candidate(1, ("SKILL_0001",)),
    ]

    ranked = rank_candidates(
        job,
        candidates,
    )

    assert [item.candidate_id for item in ranked] == [1, 2]


def test_ranked_results_preserve_explanation() -> None:
    job = make_job()

    ranked = rank_candidates(
        job,
        [make_candidate(1, ("SKILL_0001",))],
    )

    assert ranked[0].match.explanation is not None
    assert ranked[0].match.scoring_version