from __future__ import annotations

from pydantic import BaseModel, Field


class RoadmapStepRequest(BaseModel):
    skill_id: str = Field(..., min_length=1)
    priority: float = Field(..., ge=0.0)
    prerequisites: list[str] = Field(default_factory=list)


class RoadmapGenerateRequest(BaseModel):
    steps: list[RoadmapStepRequest] = Field(default_factory=list)


class RoadmapStepResponse(BaseModel):
    skill_id: str
    priority: float
    prerequisites: list[str]


class RoadmapGenerateResponse(BaseModel):
    steps: list[RoadmapStepResponse]
    scoring_version: str