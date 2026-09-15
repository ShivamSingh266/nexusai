"""API contracts for deterministic candidate/job matching."""

from datetime import datetime

from pydantic import BaseModel


class MatchingResultResponse(BaseModel):
    candidate_id: int
    job_id: int
    score: float
    component_scores: dict[str, float]
    available_components: list[str]
    omitted_components: list[str]
    taxonomy_version: str
    explanation: str
    warnings: list[str]


class MatchingResponse(BaseModel):
    data: list[MatchingResultResponse]
    meta: dict[str, str]
    model_version: str | None
    source_version: str
    generated_at: datetime
    warnings: list[str]