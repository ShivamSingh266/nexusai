"""
Member 5 - Day 1: Profile / target representations.

This module provides one common representation for both sides of matching:

    Candidate / Applicant
        -> SkillProfile(kind="candidate")

    Job / Role
        -> SkillProfile(kind="job" or "role")

Member 5 uses canonical skill IDs supplied by the shared taxonomy.
This module does NOT create or regenerate SKILL_XXXX identifiers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


ProfileKind = Literal["candidate", "job", "role"]

# Application currently stores proficiency as text.
# We keep the original value and expose a deterministic 0..1 score
# for later matching calculations.
PROFICIENCY_SCORES: dict[str, float] = {
    "beginner": 0.25,
    "intermediate": 0.50,
    "advanced": 0.75,
    "expert": 1.00,
}


def normalize_proficiency(level: str | None) -> float | None:
    """
    Convert the application's proficiency label into a normalized 0..1 score.

    Returns None when no proficiency was supplied.
    Raises ValueError for an unknown proficiency label.
    """
    if level is None:
        return None

    normalized = level.strip().lower()

    try:
        return PROFICIENCY_SCORES[normalized]
    except KeyError as exc:
        valid = ", ".join(PROFICIENCY_SCORES)
        raise ValueError(
            f"Unknown proficiency level '{level}'. "
            f"Expected one of: {valid}."
        ) from exc


@dataclass(frozen=True)
class SkillEntry:
    """
    One skill inside a candidate profile or a target profile.

    Candidate side:
        skill_id       = canonical SKILL_XXXX
        proficiency    = normalized 0..1
        evidence       = optional evidence description
        importance     = 1.0 by default

    Target side:
        skill_id       = canonical SKILL_XXXX
        importance     = how important the skill is for the target
        min_proficiency = minimum required level
    """

    skill_id: str

    # Candidate-side values
    proficiency: float | None = None
    proficiency_level: str | None = None
    evidence: str | None = None

    # Target-side values
    importance: float = 1.0
    min_proficiency: float = 0.0

    def __post_init__(self) -> None:
        if not self.skill_id:
            raise ValueError("skill_id cannot be empty.")

        if not 0.0 <= self.importance <= 1.0:
            raise ValueError("importance must be between 0 and 1.")

        if not 0.0 <= self.min_proficiency <= 1.0:
            raise ValueError("min_proficiency must be between 0 and 1.")

        if self.proficiency is not None and not 0.0 <= self.proficiency <= 1.0:
            raise ValueError("proficiency must be between 0 and 1.")


@dataclass
class SkillProfile:
    """
    Common representation consumed by Member 5 engines.

    Candidate and target/job profiles intentionally use the same shape so the
    future match() function can operate in either direction.
    """

    owner_id: int | str
    kind: ProfileKind

    skills: dict[str, SkillEntry] = field(default_factory=dict)

    # Candidate-side context
    experience_years: float | None = None
    education_level: float | None = None

    # Shared context
    location: str | None = None
    work_mode: str | None = None

    # Optional descriptive text for later semantic similarity.
    text: str | None = None

    def __post_init__(self) -> None:
        if self.experience_years is not None and self.experience_years < 0:
            raise ValueError("experience_years cannot be negative.")

        if self.education_level is not None:
            if not 0.0 <= self.education_level <= 1.0:
                raise ValueError("education_level must be between 0 and 1.")

    def add_skill(self, skill: SkillEntry) -> None:
        """Add or replace a skill by canonical skill ID."""
        self.skills[skill.skill_id] = skill

    def has_skill(self, skill_id: str) -> bool:
        """Return True when the profile contains the canonical skill ID."""
        return skill_id in self.skills