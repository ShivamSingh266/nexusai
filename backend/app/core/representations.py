"""Canonical internal representations shared by M5 calculations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SkillProfileSkill:
    """A canonical skill reference with no inferred proficiency."""

    skill_id: str
    taxonomy_version: str
    proficiency_level: str | None = None
    years_experience: int | None = None


@dataclass(frozen=True)
class SkillProfile:
    """A candidate or target profile expressed in one taxonomy version."""

    subject_id: int
    subject_type: str
    taxonomy_version: str
    skills: tuple[SkillProfileSkill, ...]
    location: str | None = None
    education: str | None = None
    experience_years: float | None = None