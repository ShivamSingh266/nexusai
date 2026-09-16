from __future__ import annotations

from pydantic import BaseModel, Field


class GapSkill(BaseModel):
    skill_id: str = Field(..., min_length=1)
    proficiency: float = Field(..., ge=0.0, le=1.0)
    proficiency_level: str = Field(..., min_length=1)
    min_proficiency: float = Field(default=0.0, ge=0.0, le=1.0)
    importance: float = Field(default=1.0, ge=0.0)
    evidence: list[str] = Field(default_factory=list)


class GapProfile(BaseModel):
    owner_id: str = Field(..., min_length=1)
    kind: str = Field(..., pattern="^(candidate|job|role)$")
    skills: list[GapSkill] = Field(default_factory=list)


class GapDemandSignal(BaseModel):
    demand: float = Field(default=1.0, ge=0.0)
    trend_multiplier: float = Field(default=1.0, ge=0.0)


class GapAnalyzeRequest(BaseModel):
    candidate: GapProfile
    target: GapProfile
    demand_signals: dict[str, GapDemandSignal] = Field(default_factory=dict)


class GapItemResponse(BaseModel):
    skill_id: str
    severity: float
    demand: float
    trend_multiplier: float
    role_importance: float
    priority: float
    explanation: str


class GapAnalyzeResponse(BaseModel):
    gaps: list[GapItemResponse]