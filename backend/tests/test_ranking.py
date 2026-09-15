import pytest

from app.core.ranking import rank_candidates
from app.core.representations import SkillEntry, SkillProfile


def make_job() -> SkillProfile:
    job = SkillProfile(
        owner_id="job-1",
        kind="job",
        experience_years=3,
        education_level=0.8,
        location="Pune",
        work_mode="remote",
        text="Python SQL data engineering",
    )

    for skill_id in ("SKILL_0001", "SKILL_0002"):
        job.add_skill(
            SkillEntry(
                skill_id=skill_id,
                proficiency=0.5,
                proficiency_level="intermediate",
                min_proficiency=0.5,
            )
        )

    return job


def make_candidate(
    candidate_id: str,
    skill_ids: list[str],
    text: str = "Python SQL data engineering",
) -> SkillProfile:
    candidate = SkillProfile(
        owner_id=candidate_id,
        kind="candidate",
        experience_years=3,
        education_level=0.8,
        location="Pune",
        work_mode="remote",
        text=text,
    )

    for skill_id in skill_ids:
        candidate.add_skill(
            SkillEntry(
                skill_id=skill_id,
                proficiency=1.0,
                proficiency_level="expert",
            )
        )

    return candidate


def test_rank_candidates_orders_by_match_score() -> None:
    job = make_job()

    strong = make_candidate(
        "candidate-strong",
        ["SKILL_0001", "SKILL_0002"],
    )

    weak = make_candidate(
        "candidate-weak",
        ["SKILL_0001"],
    )

    ranked = rank_candidates(job, [weak, strong])

    assert [item.candidate_id for item in ranked] == [
        "candidate-strong",
        "candidate-weak",
    ]


def test_ranking_is_deterministic_for_equal_candidates() -> None:
    job = make_job()

    candidate_b = make_candidate(
        "candidate-b",
        ["SKILL_0001"],
    )

    candidate_a = make_candidate(
        "candidate-a",
        ["SKILL_0001"],
    )

    ranked = rank_candidates(job, [candidate_b, candidate_a])

    assert [item.candidate_id for item in ranked] == [
        "candidate-a",
        "candidate-b",
    ]


def test_ranked_item_reuses_match_output() -> None:
    job = make_job()
    candidate = make_candidate(
        "candidate-1",
        ["SKILL_0001"],
    )

    ranked = rank_candidates(job, [candidate])

    item = ranked[0]

    assert item.match.final_score >= 0.0
    assert item.match.final_score <= 1.0
    assert item.match.scoring_version
    assert item.match.explanation is not None


def test_empty_candidate_list_returns_empty_list() -> None:
    assert rank_candidates(make_job(), []) == []


def test_ranking_preserves_explainable_components() -> None:
    job = make_job()
    candidate = make_candidate(
        "candidate-1",
        ["SKILL_0001"],
    )

    result = rank_candidates(job, [candidate])[0].match

    assert result.explanation.skill_score == pytest.approx(0.5)
    assert result.explanation.semantic_score == pytest.approx(1.0)