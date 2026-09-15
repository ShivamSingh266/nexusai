"""
Member 5 - Day 1: Weighted scoring.

Calculates the final match score from component scores using the
frozen Member 5 weights.

Missing optional components are excluded and the remaining weights
are renormalized.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class ScoreComponents:
    """Individual match-score components, each normalized to 0..1."""

    skill: float | None = None
    semantic: float | None = None
    experience: float | None = None
    education: float | None = None
    location_mode: float | None = None


def _validate_score(name: str, value: float | None) -> None:
    if value is not None and not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1.")


def calculate_weighted_score(components: ScoreComponents) -> float:
    """
    Calculate the final weighted score.

    Any component that is None is treated as unavailable. Its weight is
    removed from the denominator, so the remaining available components
    are renormalized to contribute 100% of the final score.

    Raises:
        ValueError: if any supplied component is outside the 0..1 range.
        ValueError: if all components are missing.
    """
    values = {
        "skill": (components.skill, settings.MATCH_SKILL_WEIGHT),
        "semantic": (components.semantic, settings.MATCH_SEMANTIC_WEIGHT),
        "experience": (components.experience, settings.MATCH_EXPERIENCE_WEIGHT),
        "education": (components.education, settings.MATCH_EDUCATION_WEIGHT),
        "location_mode": (
            components.location_mode,
            settings.MATCH_LOCATION_MODE_WEIGHT,
        ),
    }

    for name, (value, _) in values.items():
        _validate_score(name, value)

    available = [
        (value, weight)
        for value, weight in values.values()
        if value is not None
    ]

    if not available:
        raise ValueError("At least one score component is required.")

    weighted_total = sum(value * weight for value, weight in available)
    available_weight_total = sum(weight for _, weight in available)

    return weighted_total / available_weight_total