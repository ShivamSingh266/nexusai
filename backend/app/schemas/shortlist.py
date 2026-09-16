from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.matching import MatchingProfile


class ShortlistRequest(BaseModel):
    job: MatchingProfile
    candidates: list[MatchingProfile] = Field(default_factory=list)


class ShortlistCandidate(BaseModel):
    candidate_id: str
    final_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    scoring_version: str
    explanation: dict


class ShortlistResponse(BaseModel):
    candidates: list[ShortlistCandidate]