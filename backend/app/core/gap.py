"""
Member 5 - Day 2: Skill Gap Engine.

Compares a candidate profile against a target profile and ranks missing
skills using the required baseline:

    priority =
        normalized_demand
        * trend_multiplier
        * gap_severity
        * role_importance

Canonical skill IDs are supplied by the shared taxonomy pipeline.
This module does not create or regenerate skill IDs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.core.representations import SkillProfile


@dataclass(frozen=True)
class DemandSignal:
    """Demand information for one canonical skill."""

    demand: float = 1.0
    trend_multiplier: float = 1.0


@dataclass(frozen=True)
class SkillGap:
    """One missing/insufficient skill for a candidate."""

    skill_id: str
    severity: float
    demand: float
    trend_multiplier: float
    role_importance: float
    priority: float
    explanation: str


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(value, maximum))


def calculate_gap_severity(
    candidate_proficiency: float | None,
    required_proficiency: float,
) -> float:
    """
    Calculate how severe a skill gap is.

    If the candidate has no usable proficiency, severity is 1.0.

    Otherwise:

        severity = 1 - (candidate / required)

    capped to 0..1.

    A candidate meeting or exceeding the requirement has severity 0.
    """
    if required_proficiency < 0.0 or required_proficiency > 1.0:
        raise ValueError("required_proficiency must be between 0 and 1.")

    if candidate_proficiency is None:
        return 1.0

    if candidate_proficiency < 0.0 or candidate_proficiency > 1.0:
        raise ValueError("candidate_proficiency must be between 0 and 1.")

    if required_proficiency == 0.0:
        return 0.0

    return _clamp(1.0 - (candidate_proficiency / required_proficiency))


def calculate_gap_priority(
    *,
    demand: float,
    trend_multiplier: float,
    severity: float,
    role_importance: float,
) -> float:
    """
    Apply the frozen Member 5 gap-priority formula.
    """
    values = {
        "demand": demand,
        "trend_multiplier": trend_multiplier,
        "severity": severity,
        "role_importance": role_importance,
    }

    for name, value in values.items():
        if value < 0.0:
            raise ValueError(f"{name} cannot be negative.")

    return demand * trend_multiplier * severity * role_importance


def analyze_gap(
    candidate: SkillProfile,
    target: SkillProfile,
    demand_signals: dict[str, DemandSignal] | None = None,
) -> list[SkillGap]:
    """
    Compare candidate skills with target requirements.

    A skill is included in the result only when it is missing or the
    candidate's proficiency is below the target's minimum proficiency.

    Existing taxonomy overlap remains authoritative: this function works
    on canonical skill IDs and does not perform text-to-skill resolution.
    """
    if candidate.kind != "candidate":
        raise ValueError("candidate profile must have kind='candidate'.")

    if target.kind not in {"job", "role"}:
        raise ValueError("target profile must have kind='job' or kind='role'.")

    demand_signals = demand_signals or {}

    gaps: list[SkillGap] = []

    for skill_id, required in target.skills.items():
        actual = candidate.skills.get(skill_id)

        actual_proficiency = actual.proficiency if actual else None
        required_proficiency = required.min_proficiency

        # Explicit overlap first: meeting the required level means no gap.
        if (
            actual_proficiency is not None
            and actual_proficiency >= required_proficiency
        ):
            continue

        severity = calculate_gap_severity(
            actual_proficiency,
            required_proficiency,
        )

        signal = demand_signals.get(skill_id, DemandSignal())

        priority = calculate_gap_priority(
            demand=signal.demand,
            trend_multiplier=signal.trend_multiplier,
            severity=severity,
            role_importance=required.importance,
        )

        if actual is None:
            explanation = (
                f"Skill {skill_id} is missing from the candidate profile. "
                f"Required proficiency is {required_proficiency:.2f}."
            )
        else:
            explanation = (
                f"Skill {skill_id} is below the required proficiency: "
                f"candidate={actual_proficiency:.2f}, "
                f"required={required_proficiency:.2f}."
            )

        gaps.append(
            SkillGap(
                skill_id=skill_id,
                severity=severity,
                demand=signal.demand,
                trend_multiplier=signal.trend_multiplier,
                role_importance=required.importance,
                priority=priority,
                explanation=explanation,
            )
        )

    # Deterministic ranking:
    # higher priority first, then skill ID for stable output.
    gaps.sort(key=lambda gap: (-gap.priority, gap.skill_id))

    return gaps