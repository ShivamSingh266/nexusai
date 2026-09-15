import pytest

from app.core.gap import DemandSignal
from app.core.representations import SkillEntry, SkillProfile
from app.core.what_if import career_what_if


def make_candidate() -> SkillProfile:
    candidate = SkillProfile(
        owner_id="candidate-1",
        kind="candidate",
        experience_years=3,
        education_level=0.8,
        location="Pune",
        work_mode="remote",
        text="Python SQL",
    )

    candidate.add_skill(
        SkillEntry(
            skill_id="SKILL_0001",
            proficiency=1.0,
            proficiency_level="expert",
        )
    )

    return candidate


def make_job() -> SkillProfile:
    job = SkillProfile(
        owner_id="job-1",
        kind="job",
        experience_years=3,
        education_level=0.8,
        location="Pune",
        work_mode="remote",
        text="Python SQL machine learning",
    )

    job.add_skill(
        SkillEntry(
            skill_id="SKILL_0001",
            proficiency=0.5,
            proficiency_level="intermediate",
            min_proficiency=0.5,
        )
    )

    job.add_skill(
        SkillEntry(
            skill_id="SKILL_0002",
            proficiency=0.5,
            proficiency_level="intermediate",
            min_proficiency=0.5,
        )
    )

    return job


def test_what_if_reduces_gaps_when_added_skill_is_relevant() -> None:
    candidate = make_candidate()
    job = make_job()

    added = {
        "SKILL_0002": SkillEntry(
            skill_id="SKILL_0002",
            proficiency=1.0,
            proficiency_level="expert",
        )
    }

    result = career_what_if(candidate, job, added)

    assert result.baseline_gaps
    assert result.hypothetical_gaps == []
    assert result.gap_count_change == -1


def test_what_if_improves_match_score() -> None:
    candidate = make_candidate()
    job = make_job()

    added = {
        "SKILL_0002": SkillEntry(
            skill_id="SKILL_0002",
            proficiency=1.0,
            proficiency_level="expert",
        )
    }

    result = career_what_if(candidate, job, added)

    assert result.hypothetical_match.final_score > result.baseline_match.final_score
    assert result.match_score_change > 0.0


def test_what_if_does_not_mutate_original_candidate() -> None:
    candidate = make_candidate()
    job = make_job()

    added = {
        "SKILL_0002": SkillEntry(
            skill_id="SKILL_0002",
            proficiency=1.0,
            proficiency_level="expert",
        )
    }

    career_what_if(candidate, job, added)

    assert "SKILL_0002" not in candidate.skills


def test_what_if_returns_scoring_versions() -> None:
    result = career_what_if(
        make_candidate(),
        make_job(),
        {
            "SKILL_0002": SkillEntry(
                skill_id="SKILL_0002",
                proficiency=1.0,
                proficiency_level="expert",
            )
        },
    )

    assert result.baseline_match.scoring_version
    assert result.hypothetical_match.scoring_version


def test_what_if_preserves_demand_based_gap_priority() -> None:
    candidate = make_candidate()
    job = make_job()

    demand_signals = {
        "SKILL_0002": DemandSignal(
            demand=2.0,
            trend_multiplier=1.5,
        )
    }

    result = career_what_if(
        candidate,
        job,
        {},
        demand_signals,
    )

    assert len(result.baseline_gaps) == 1
    assert result.baseline_gaps[0].priority == pytest.approx(
        2.0 * 1.5 * 1.0 * 1.0
    )


def test_empty_what_if_keeps_scores_unchanged() -> None:
    candidate = make_candidate()
    job = make_job()

    result = career_what_if(
        candidate,
        job,
        {},
    )

    assert result.match_score_change == pytest.approx(0.0)
    assert result.gap_count_change == 0
    assert result.baseline_match.final_score == pytest.approx(
        result.hypothetical_match.final_score
    )