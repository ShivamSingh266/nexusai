import pytest

from app.core.gap import (
    DemandSignal,
    analyze_gap,
    calculate_gap_priority,
    calculate_gap_severity,
)
from app.core.representations import SkillEntry, SkillProfile


def make_candidate() -> SkillProfile:
    profile = SkillProfile(owner_id=1, kind="candidate")

    profile.add_skill(
        SkillEntry(
            skill_id="SKILL_0001",
            proficiency=0.80,
        )
    )

    return profile


def make_target() -> SkillProfile:
    profile = SkillProfile(owner_id=10, kind="role")

    profile.add_skill(
        SkillEntry(
            skill_id="SKILL_0001",
            importance=1.0,
            min_proficiency=0.60,
        )
    )

    profile.add_skill(
        SkillEntry(
            skill_id="SKILL_0002",
            importance=0.80,
            min_proficiency=0.70,
        )
    )

    return profile


def test_no_gap_when_candidate_meets_requirement() -> None:
    gaps = analyze_gap(make_candidate(), make_target())

    assert all(g.skill_id != "SKILL_0001" for g in gaps)
    assert any(g.skill_id == "SKILL_0002" for g in gaps)


def test_missing_skill_has_full_severity() -> None:
    gaps = analyze_gap(
        make_candidate(),
        make_target(),
    )

    missing = next(g for g in gaps if g.skill_id == "SKILL_0002")

    assert missing.severity == pytest.approx(1.0)


def test_partial_skill_gap_severity() -> None:
    severity = calculate_gap_severity(
        candidate_proficiency=0.35,
        required_proficiency=0.70,
    )

    assert severity == pytest.approx(0.50)


def test_gap_priority_formula() -> None:
    priority = calculate_gap_priority(
        demand=0.8,
        trend_multiplier=1.2,
        severity=0.5,
        role_importance=0.9,
    )

    assert priority == pytest.approx(0.432)


def test_demand_and_trend_change_ranking() -> None:
    candidate = SkillProfile(owner_id=1, kind="candidate")

    target = SkillProfile(owner_id=2, kind="role")

    target.add_skill(
        SkillEntry(
            skill_id="SKILL_0001",
            importance=1.0,
            min_proficiency=0.5,
        )
    )

    target.add_skill(
        SkillEntry(
            skill_id="SKILL_0002",
            importance=1.0,
            min_proficiency=0.5,
        )
    )

    gaps = analyze_gap(
        candidate,
        target,
        demand_signals={
            "SKILL_0001": DemandSignal(
                demand=0.5,
                trend_multiplier=1.0,
            ),
            "SKILL_0002": DemandSignal(
                demand=1.0,
                trend_multiplier=1.5,
            ),
        },
    )

    assert gaps[0].skill_id == "SKILL_0002"


def test_invalid_score_inputs_raise() -> None:
    with pytest.raises(ValueError):
        calculate_gap_severity(
            candidate_proficiency=1.2,
            required_proficiency=0.8,
        )

    with pytest.raises(ValueError):
        calculate_gap_priority(
            demand=-1.0,
            trend_multiplier=1.0,
            severity=1.0,
            role_importance=1.0,
        )