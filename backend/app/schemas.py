from typing import Optional
from pydantic import BaseModel


class GapAnalyzeRequest(BaseModel):
    candidate_id: str
    target_role_id: str
    district_id: Optional[str] = None
    sector: Optional[str] = None
    persist: bool = True


class SkillGapOut(BaseModel):
    skill_id: str
    gap_severity: float
    normalized_demand: float
    trend_multiplier: float
    role_importance: float
    priority: float
    explanation: dict


class GapAnalyzeResponse(BaseModel):
    candidate_id: str
    target_role_id: str
    scoring_version: str
    gaps: list[SkillGapOut]


class RoadmapGenerateRequest(BaseModel):
    candidate_id: str
    target_role_id: str
    district_id: Optional[str] = None
    sector: Optional[str] = None


class RoadmapStepOut(BaseModel):
    skill_id: str
    course_id: Optional[str]
    project: Optional[str]
    step_order: int
    duration: Optional[str]


class RoadmapGenerateResponse(BaseModel):
    roadmap_id: str
    model_version: str
    steps: list[RoadmapStepOut]


class MatchRequest(BaseModel):
    candidate_id: str
    job_id: str
    persist: bool = True


class MatchComponentsOut(BaseModel):
    skill_coverage: Optional[float]
    semantic: Optional[float]
    experience: Optional[float]
    education: Optional[float]
    location: Optional[float]


class MatchResponse(BaseModel):
    candidate_id: str
    job_id: str
    score: float
    components: MatchComponentsOut
    weights_used: dict
    matched_skills: list
    missing_skills: list
    explanation: dict
    scoring_version: str


class RankJobsRequest(BaseModel):
    candidate_id: str
    job_ids: Optional[list[str]] = None  # None = all open jobs
    top_n: Optional[int] = None


class CandidatesForJobQuery(BaseModel):
    top_n: Optional[int] = None


class ShortlistCreateRequest(BaseModel):
    job_id: str
    recruiter_id: str
    candidate_ids: list[str]
    top_n: Optional[int] = None


class ShortlistItemOut(BaseModel):
    candidate_id: str
    rank: int
    score: float
    decision: str


class ShortlistCreateResponse(BaseModel):
    shortlist_id: str
    job_id: str
    items: list[ShortlistItemOut]


class WhatIfRequest(BaseModel):
    candidate_id: str
    target_role_id: str
    hypothetical_skills: dict[str, float]  # skill_id -> proficiency 0..1
    district_id: Optional[str] = None
    sector: Optional[str] = None


class WhatIfResponse(BaseModel):
    baseline_score: float
    hypothetical_score: float
    score_delta: float
    baseline_gap_count: int
    hypothetical_gap_count: int
    gap_priority_removed: float
    resolved_skill_ids: list[str]
