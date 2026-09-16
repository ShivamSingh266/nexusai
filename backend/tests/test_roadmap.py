import pytest

from app.core.roadmap import (
    RoadmapCycleError,
    RoadmapStep,
    sequence_roadmap,
    validate_prerequisite_dag,
)


def test_valid_dag_is_accepted() -> None:
    validate_prerequisite_dag(
        {
            "SKILL_B": ["SKILL_A"],
            "SKILL_C": ["SKILL_B"],
        }
    )


def test_cycle_is_rejected() -> None:
    with pytest.raises(RoadmapCycleError):
        validate_prerequisite_dag(
            {
                "SKILL_A": ["SKILL_B"],
                "SKILL_B": ["SKILL_A"],
            }
        )


def test_transitive_cycle_is_rejected() -> None:
    with pytest.raises(RoadmapCycleError):
        validate_prerequisite_dag(
            {
                "SKILL_A": ["SKILL_C"],
                "SKILL_B": ["SKILL_A"],
                "SKILL_C": ["SKILL_B"],
            }
        )


def test_prerequisite_comes_before_dependent() -> None:
    steps = [
        RoadmapStep(
            skill_id="SKILL_C",
            priority=1.0,
            prerequisites=("SKILL_B",),
        ),
        RoadmapStep(
            skill_id="SKILL_B",
            priority=1.0,
            prerequisites=("SKILL_A",),
        ),
        RoadmapStep(
            skill_id="SKILL_A",
            priority=0.5,
            prerequisites=(),
        ),
    ]

    ordered = sequence_roadmap(steps)

    assert [step.skill_id for step in ordered] == [
        "SKILL_A",
        "SKILL_B",
        "SKILL_C",
    ]


def test_priority_orders_independent_skills() -> None:
    steps = [
        RoadmapStep(
            skill_id="SKILL_LOW",
            priority=0.2,
            prerequisites=(),
        ),
        RoadmapStep(
            skill_id="SKILL_HIGH",
            priority=0.9,
            prerequisites=(),
        ),
    ]

    ordered = sequence_roadmap(steps)

    assert [step.skill_id for step in ordered] == [
        "SKILL_HIGH",
        "SKILL_LOW",
    ]


def test_skill_id_breaks_equal_priority_ties() -> None:
    steps = [
        RoadmapStep(
            skill_id="SKILL_Z",
            priority=0.5,
            prerequisites=(),
        ),
        RoadmapStep(
            skill_id="SKILL_A",
            priority=0.5,
            prerequisites=(),
        ),
    ]

    ordered = sequence_roadmap(steps)

    assert [step.skill_id for step in ordered] == [
        "SKILL_A",
        "SKILL_Z",
    ]


def test_empty_roadmap_returns_empty_list() -> None:
    assert sequence_roadmap([]) == []


def test_missing_prerequisite_is_not_rejected() -> None:
    steps = [
        RoadmapStep(
            skill_id="SKILL_B",
            priority=1.0,
            prerequisites=("SKILL_EXTERNAL",),
        ),
    ]

    ordered = sequence_roadmap(steps)

    assert [step.skill_id for step in ordered] == ["SKILL_B"]