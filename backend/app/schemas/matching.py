from __future__ import annotations

from pydantic import BaseModel, Field


class MatchingSkill(BaseModel):
    skill_id: str = Field(..., min_length=1)
    proficiency: float = Field(..., ge=0.0, le=1.0)
    proficiency_level: str = Field(..., min_length=1)
    min_proficiency: float = Field(default=0.0, ge=0.0, le=1.0)
    importance: float = Field(default=1.0, ge=0.0)
    evidence: list[str] = Field(default_factory=list)


class MatchingProfile(BaseModel):
    owner_id: str = Field(..., min_length=1)
    kind: str = Field(..., pattern="^(candidate|job|role)$")
    skills: list[MatchingSkill] = Field(default_factory=list)
    experience_years: float | None = Field(default=None, ge=0.0)
    education_level: float | None = Field(default=None, ge=0.0, le=1.0)
    location: str | None = None
    work_mode: str | None = None
    text: str = ""


class MatchRequest(BaseModel):
    candidate: MatchingProfile
    target: MatchingProfile


class MatchExplanationResponse(BaseModel):
    skill_score: float
    semantic_score: float
    experience_score: float | None
    education_score: float | None
    location_mode_score: float | None
    weights: dict[str, float]
    final_score: float


class MatchResponse(BaseModel):
    matched_skills: list[str]
    missing_skills: list[str]
    explanation: MatchExplanationResponse
    final_score: float
    scoring_version: str